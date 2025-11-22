"""Reward calculation LLM for evaluating agent performance."""
from typing import Dict, Any, List
from openpipe import OpenAI
from src.config import Config
from src.scenarios import AttackScenario
from src.prompts.reward import get_reward_evaluation_prompt, get_reward_system_prompt


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
                "HTTP-Referer": "https://github.com/samx3499/watson",
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
        
        prompt = get_reward_evaluation_prompt(
            scenario_name=scenario.name,
            scenario_type=scenario.attack_type,
            scenario_description=scenario.description,
            expected_indicators=scenario.expected_indicators,
            conversation_summary=conversation_summary,
            tool_calls_made=tool_calls_made
        )
        
        # Build request
        request_params = {
            "model": Config.REWARD_MODEL,
            "messages": [
                {"role": "system", "content": get_reward_system_prompt()},
                {"role": "user", "content": prompt + "\n\nIMPORTANT: Respond with ONLY valid JSON, no other text."}
            ],
            "temperature": 0.3,
        }
        
        # Add JSON mode if supported
        if "gemini" not in Config.REWARD_MODEL.lower():
            request_params["response_format"] = {"type": "json_object"}
        
        if Config.OPENPIPE_API_KEY:
            request_params["openpipe"] = {
                "tags": {
                    "component": Config.REWARD_TAG,
                    "scenario_id": scenario.id,
                },
                "log_request": True,
            }
        
        response = self.client.chat.completions.create(**request_params)
        
        import json
        reward_data = json.loads(response.choices[0].message.content)
        
        return {
            **reward_data,
            "scenario_id": scenario.id,
            "scenario_difficulty": scenario.difficulty,
            "tool_calls_made": tool_calls_made,
        }
    
    def calculate_incremental_reward(
        self,
        scenario: AttackScenario,
        query: str,
        response: str,
        query_number: int,  # noqa: ARG002
        total_queries: int
    ) -> float:
        """
        Calculate a simple incremental reward for a single query-response pair.
        This is a lightweight heuristic reward, not a full LLM evaluation.
        
        Args:
            scenario: The attack scenario
            query: The query that was made
            response: The response received
            query_number: Which query this is (1-indexed)
            total_queries: Total number of queries made so far
            
        Returns:
            A reward score (typically -1 to +1)
        """
        reward = 0.0
        
        # Check if query is relevant to the scenario
        query_lower = query.lower()
        scenario_keywords = [
            scenario.name.lower(),
            scenario.attack_type.lower(),
        ] + [ind.lower() for ind in scenario.expected_indicators]
        
        # Reward for relevant queries
        if any(keyword in query_lower for keyword in scenario_keywords):
            reward += 0.3
        
        # Check if response contains useful information
        response_lower = response.lower()
        if len(response) > 50:  # Substantial response
            reward += 0.2
        
        # Check if response mentions indicators
        for indicator in scenario.expected_indicators:
            if indicator.lower() in response_lower:
                reward += 0.5
        
        # Penalize very short or empty queries
        if len(query) < 10:
            reward -= 0.2
        
        # Small penalty for too many queries (efficiency)
        if total_queries > 10:
            reward -= 0.1
        
        # Slight bonus for early relevant queries (exploration)
        if query_number <= 3 and reward > 0:
            reward += 0.1
        
        # Normalize to roughly -1 to +1 range
        return max(-1.0, min(1.0, reward))
    
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

