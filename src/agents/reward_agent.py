"""Reward Agent - Calculates rewards for agent performance."""

from typing import Any, Dict, List

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.prompts.reward import (
    get_incremental_reward_prompt,
    get_reward_evaluation_prompt,
    get_reward_system_prompt,
)
from src.scenarios import AttackScenario
from src.utils.config import Config


class RewardAgent:
    """
    LLM that calculates rewards for agent performance.
    Evaluates how well the agent discovered the attack.
    """

    def __init__(self):
        """Initialize the reward calculation agent."""
        self.agent = Agent(
            model=OpenAIChat(
                id=Config.REWARD_MODEL,
                api_key=Config.OPENROUTER_API_KEY,
                base_url=Config.OPENROUTER_BASE_URL,
                temperature=0.3,
            ),
            instructions=get_reward_system_prompt(),
            markdown=True,
        )

    def calculate_reward(
        self,
        scenario: AttackScenario,
        agent_investigation: Dict[str, Any],
        tool_calls_made: int,
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
        conversation_summary = self._summarize_conversation(
            agent_investigation.get("conversation_history", [])
        )

        prompt = get_reward_evaluation_prompt(
            scenario_name=scenario.name,
            scenario_type=scenario.attack_type,
            scenario_description=scenario.description,
            expected_indicators=scenario.expected_indicators,
            conversation_summary=conversation_summary,
            tool_calls_made=tool_calls_made,
        )

        # Add JSON requirement
        prompt += "\n\nIMPORTANT: Respond with ONLY valid JSON, no other text."

        # Call agent
        response = self.agent.run(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        # Parse JSON response
        import json

        try:
            reward_data = json.loads(content)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            reward_data = {
                "attack_detection": 0,
                "indicator_discovery": 0,
                "query_quality": 0,
                "efficiency": 0,
                "thoroughness": 0,
                "total_reward": 0,
                "reasoning": "Failed to parse reward response",
            }

        return {
            **reward_data,
            "tool_calls_made": tool_calls_made,
        }

    def calculate_incremental_reward(
        self,
        scenario: AttackScenario,
        query: str,
        response: str,
        query_number: int,
        total_queries: int,  # noqa: ARG002
    ) -> float:
        """
        Calculate incremental reward using LLM evaluation.

        Args:
            scenario: The attack scenario
            query: The query that was made
            response: The response received
            query_number: Which query this is (1-indexed)
            total_queries: Total number of queries made so far

        Returns:
            A reward score (typically -1 to +1)
        """
        prompt = get_incremental_reward_prompt(
            scenario_name=scenario.name,
            scenario_type=scenario.attack_type,
            scenario_description=scenario.description,
            expected_indicators=scenario.expected_indicators,
            query=query,
            response=response,
            query_number=query_number,
        )

        prompt += "\n\nIMPORTANT: Respond with ONLY valid JSON, no other text."

        # Call agent
        try:
            llm_response = self.agent.run(prompt)
            content = (
                llm_response.content
                if hasattr(llm_response, "content")
                else str(llm_response)
            )

            # Parse JSON response
            import json

            try:
                # Clean content (remove potential markdown code blocks)
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1]

                reward_data = json.loads(content.strip())
                score = float(reward_data.get("score", 0.0))

                # Clamp score
                return max(-1.0, min(1.0, score))
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing reward response: {e}")
                return 0.0
        except Exception as e:
            print(f"Error calling reward agent: {e}")
            return 0.0

    def _summarize_conversation(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Summarize the conversation history for reward evaluation."""
        summary_parts = []

        for i, msg in enumerate(conversation_history):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls", [])

            if role == "user":
                summary_parts.append(f"Step {i + 1}: User: {content}")
            elif role == "assistant":
                if tool_calls:
                    for tc in tool_calls:
                        func_name = tc.get("function", {}).get("name", "unknown")
                        func_args = tc.get("function", {}).get("arguments", "{}")
                        summary_parts.append(
                            f"Step {i + 1}: Agent called {func_name} with: {func_args}"
                        )
                elif content:
                    summary_parts.append(f"Step {i + 1}: Agent: {content}")
            elif role == "tool":
                summary_parts.append(
                    f"Step {i + 1}: Query Result: {content[:200]}..."
                )  # Truncate long results

        return "\n".join(summary_parts)
