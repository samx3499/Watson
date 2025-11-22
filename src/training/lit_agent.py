"""LitAgent wrapper for Agent-lightning training."""

from typing import Any, Dict

import agentlightning as agl

from src.agents.db_agent import DatabaseAgent
from src.agents.reward_agent import RewardAgent
from src.agents.watson_agent import WatsonAgent
from src.scenarios import AttackScenario


class LitWatsonAgent(agl.LitAgent[Dict[str, Any]]):
    """
    Agent-lightning wrapper for Watson agent.

    This bridges the Watson agent with Agent-lightning's training infrastructure.
    The rollout method runs a single investigation episode and returns a reward.
    """

    def __init__(self, max_tool_calls: int = 100):
        """
        Initialize the LitWatsonAgent.

        Args:
            max_tool_calls: Maximum number of tool calls allowed per episode
        """
        self.max_tool_calls = max_tool_calls

    def rollout(
        self,
        task: Dict[str, Any],
        resources: agl.NamedResources,
        rollout: agl.Rollout,
    ) -> float | None:
        """
        Run a single investigation episode.

        Args:
            task: Dictionary containing the scenario data
            resources: Named resources from VERL (includes "main_llm")
            rollout: Rollout metadata

        Returns:
            Reward score (float) or None if episode failed
        """
        # Extract scenario from task
        scenario = AttackScenario(
            id=task["id"],
            name=task["name"],
            description=task["description"],
            attack_type=task["attack_type"],
            environment_knowledge=task["environment_knowledge"],
            expected_indicators=task["expected_indicators"],
            difficulty=task.get("difficulty", 5),
        )

        # Get LLM resource from VERL
        llm: agl.LLM = resources["main_llm"]

        # Get the base URL for this rollout (VERL provides per-rollout endpoints)
        base_url = llm.get_base_url(rollout.rollout_id, rollout.attempt.attempt_id)

        # Create database agent (environment)
        db_agent = DatabaseAgent(scenario)

        # Create reward agent
        reward_agent = RewardAgent()

        # Track metrics
        cumulative_reward = 0.0
        queries_made = 0

        # Create query callback
        def query_callback(query: str) -> str:
            """Callback for Watson agent queries."""
            nonlocal cumulative_reward, queries_made
            queries_made += 1

            # Execute query
            response = db_agent.query(query)

            # Calculate incremental reward
            inc_reward = reward_agent.calculate_incremental_reward(
                scenario=scenario,
                query=query,
                response=response,
                query_number=queries_made,
                total_queries=queries_made,
            )
            cumulative_reward += inc_reward

            return response

        # Create Watson agent with VERL's LLM endpoint
        watson_agent = WatsonAgent(
            max_tool_calls=self.max_tool_calls,
            model_id=llm.model,
            api_key="",  # Not needed for VERL endpoint
            base_url=base_url,
        )

        # Run investigation
        try:
            investigation_result = watson_agent.investigate(
                query_callback=query_callback,
                initial_prompt="Begin investigating the logs to uncover any security incidents.",
                verbose=False,
            )

            # Calculate final reward
            reward_data = reward_agent.calculate_reward(
                scenario=scenario,
                agent_investigation=investigation_result,
                tool_calls_made=investigation_result.get("tool_calls_made", 0),
            )

            # Add final reward to cumulative reward
            final_reward = reward_data.get("total_reward", 0.0)
            cumulative_reward += final_reward

            return float(cumulative_reward)

        except Exception as e:
            # Log error but don't crash - return None to signal failure
            print(f"Error in rollout: {e}")
            return None
