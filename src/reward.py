"""Reward calculation LLM for evaluating agent performance."""
from typing import Dict, Any, List
from openpipe import OpenAI
from src.config import Config
from src.scenarios import AttackScenario


class RewardLLM:
    """
    LLM that calculates rewards for agent performance.
    Evaluates how well the agent discovered the attack.
    """
    
    def __init__(self):
        """Initialize the reward calculation LLM."""
        # Use OpenRouter (OpenAI-compatible) with optional OpenPipe logging
        openpipe_config = {}
        if Config.OPENPIPE_API_KEY:
            openpipe_config = {
                "api_key": Config.OPENPIPE_API_KEY,
                "base_url": Config.OPENPIPE_BASE_URL,
            }
        
        self.client = OpenAI(
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": "https://github.com/yourusername/watson",
                "X-Title": "Watson Reward",
            },
            openpipe=openpipe_config if openpipe_config else None
        )
    
    def calculate_reward(
        self,
        scenario: AttackScenario,
        agent_investigation: Dict[str, Any],
        tool_calls_made: int
    ) -> Dict[str, Any]:
        """
        Calculate reward for agent's investigation.
        
        Args:
            scenario: The attack scenario that was investigated
            agent_investigation: The agent's investigation results
            tool_calls_made: Number of tool calls the agent made
            
        Returns:
            Dictionary containing reward breakdown and total reward
        """
        # Build prompt for reward calculation
        conversation_summary = self._summarize_conversation(agent_investigation.get("conversation_history", []))
        
        prompt = f"""You are evaluating a security analyst's investigation of a potential security incident.

ATTACK SCENARIO:
Name: {scenario.name}
Type: {scenario.attack_type}
Description: {scenario.description}

EXPECTED INDICATORS (what the analyst should have discovered):
{chr(10).join(f"- {indicator}" for indicator in scenario.expected_indicators)}

INVESTIGATION SUMMARY:
{conversation_summary}

TOOL CALLS MADE: {tool_calls_made}

Evaluate the investigation on the following criteria (each scored 0-10):

1. ATTACK DETECTION (0-10): Did the analyst identify the attack? How accurately?
2. INDICATOR DISCOVERY (0-10): How many expected indicators were discovered?
3. QUERY QUALITY (0-10): Were the queries well-formed and effective?
4. EFFICIENCY (0-10): Was the investigation efficient (fewer tool calls = better, but not at expense of thoroughness)?
5. THOROUGHNESS (0-10): Was the investigation comprehensive?

Provide your evaluation as a JSON object with this structure:
{{
    "attack_detection": <score 0-10>,
    "indicator_discovery": <score 0-10>,
    "query_quality": <score 0-10>,
    "efficiency": <score 0-10>,
    "thoroughness": <score 0-10>,
    "total_reward": <sum of all scores>,
    "reasoning": "<brief explanation of scores>"
}}

Be strict but fair. Reward good detective work and penalize missed attacks or inefficient queries.
"""
        
        response = self.client.chat.completions.create(
            model=Config.REWARD_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert security analyst evaluating investigations. Provide detailed, fair evaluations."},
                {"role": "user", "content": prompt}
            ],
            openpipe={
                "tags": {
                    "component": Config.REWARD_TAG,
                    "scenario_id": scenario.id,
                },
                "log_request": bool(Config.OPENPIPE_API_KEY),  # Only log if API key is set
            } if Config.OPENPIPE_API_KEY else None,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        import json
        reward_data = json.loads(response.choices[0].message.content)
        
        return {
            **reward_data,
            "scenario_id": scenario.id,
            "scenario_difficulty": scenario.difficulty,
            "tool_calls_made": tool_calls_made,
        }
    
    def _summarize_conversation(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Summarize the conversation history for reward evaluation."""
        summary_parts = []
        
        for i, msg in enumerate(conversation_history):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls", [])
            
            if role == "user":
                summary_parts.append(f"Step {i+1}: User: {content}")
            elif role == "assistant":
                if tool_calls:
                    for tc in tool_calls:
                        func_name = tc.get("function", {}).get("name", "unknown")
                        func_args = tc.get("function", {}).get("arguments", "{}")
                        summary_parts.append(f"Step {i+1}: Agent called {func_name} with: {func_args}")
                elif content:
                    summary_parts.append(f"Step {i+1}: Agent: {content}")
            elif role == "tool":
                summary_parts.append(f"Step {i+1}: Query Result: {content[:200]}...")  # Truncate long results
        
        return "\n".join(summary_parts)

