"""Episode runner that orchestrates agent, environment, and reward."""
from typing import Dict, Any, Optional

try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False

from src.agent import AgentLLM
from src.environment import EnvironmentLLM
from src.reward import RewardLLM
from src.scenarios import AttackScenario
from src.config import Config


class EpisodeRunner:
    """
    Runs a single episode: agent investigates, environment responds, reward is calculated.
    """
    
    def __init__(self, use_wandb: bool = True):
        """
        Initialize the episode runner.
        
        Args:
            use_wandb: Whether to log to WandB (requires WANDB_API_KEY)
        """
        self.agent = AgentLLM(max_tool_calls=100)
        self.reward_llm = RewardLLM()
        self.use_wandb = use_wandb and WANDB_AVAILABLE and Config.WANDB_API_KEY is not None
        
        if self.use_wandb:
            wandb.init(
                project=Config.WANDB_PROJECT,
                entity=Config.WANDB_ENTITY,
                config={
                    "agent_model": Config.AGENT_MODEL,
                    "environment_model": Config.ENVIRONMENT_MODEL,
                    "reward_model": Config.REWARD_MODEL,
                }
            )
    
    def run_episode(self, scenario: AttackScenario) -> Dict[str, Any]:
        """
        Run a single episode with a given scenario.
        
        Args:
            scenario: The attack scenario to investigate
            
        Returns:
            Dictionary containing episode results including reward
        """
        # Initialize environment for this scenario
        environment = EnvironmentLLM(scenario)
        
        # Define query callback that uses the environment
        def query_callback(query: str) -> str:
            return environment.query(query, context=environment.conversation_history)
        
        # Run agent investigation
        investigation_result = self.agent.investigate(
            scenario_description=scenario.description,
            query_callback=query_callback
        )
        
        # Calculate reward
        reward_result = self.reward_llm.calculate_reward(
            scenario=scenario,
            agent_investigation=investigation_result,
            tool_calls_made=investigation_result["tool_calls_made"]
        )
        
        episode_result = {
            "scenario_id": scenario.id,
            "scenario_name": scenario.name,
            "investigation": investigation_result,
            "reward": reward_result,
        }
        
        # Log to WandB
        if self.use_wandb:
            wandb.log({
                "episode/scenario_id": scenario.id,
                "episode/scenario_name": scenario.name,
                "episode/scenario_difficulty": scenario.difficulty,
                "episode/tool_calls_made": investigation_result["tool_calls_made"],
                "reward/total": reward_result.get("total_reward", 0),
                "reward/attack_detection": reward_result.get("attack_detection", 0),
                "reward/indicator_discovery": reward_result.get("indicator_discovery", 0),
                "reward/query_quality": reward_result.get("query_quality", 0),
                "reward/efficiency": reward_result.get("efficiency", 0),
                "reward/thoroughness": reward_result.get("thoroughness", 0),
            })
        
        return episode_result

