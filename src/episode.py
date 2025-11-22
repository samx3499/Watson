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
from src.colors import Colors, colorize


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
    
    def run_episode(self, scenario: AttackScenario, verbose: bool = True) -> Dict[str, Any]:
        """
        Run a single episode with a given scenario.
        
        Args:
            scenario: The attack scenario to investigate
            verbose: Whether to print detailed episode flow
            
        Returns:
            Dictionary containing episode results including reward
        """
        # Print episode start (without revealing scenario details)
        if verbose:
            print("\n" + colorize("="*60, Colors.HEADER))
            print(colorize("EPISODE START", Colors.HEADER + Colors.BOLD))
            print(colorize("="*60, Colors.HEADER) + "\n")
        
        # Initialize environment for this scenario
        environment = EnvironmentLLM(scenario)
        
        # Track queries and responses for verbose output and incremental rewards
        query_response_pairs = []
        incremental_rewards = []
        total_incremental_reward = 0.0
        
        # Track current query for reward calculation
        current_query_index = 0
        
        # Define query callback that uses the environment
        def query_callback(query: str) -> str:
            nonlocal current_query_index, total_incremental_reward
            result = environment.query(query, context=environment.conversation_history)
            query_response_pairs.append((query, result))
            current_query_index += 1
            
            # Calculate incremental reward
            incremental_reward = self.reward_llm.calculate_incremental_reward(
                scenario=scenario,
                query=query,
                response=result,
                query_number=current_query_index,
                total_queries=current_query_index
            )
            incremental_rewards.append(incremental_reward)
            total_incremental_reward += incremental_reward
            
            return result
        
        # Define query print callback for verbose output
        def query_print_callback(query: str, result: Optional[str]) -> None:
            nonlocal incremental_rewards, total_incremental_reward
            if result is None:
                # Query is being executed
                print(colorize(f"Watson queried", Colors.QUERY + Colors.BOLD) + f": \"{colorize(query, Colors.QUERY)}\"")
            else:
                # Result received - always print this
                result_preview = result[:200] + ('...' if len(result) > 200 else '')
                print(colorize(f"DB responded", Colors.RESPONSE + Colors.BOLD) + f": \"{colorize(result_preview, Colors.RESPONSE)}\"")
                
                # Show incremental reward (should be available now since query_callback was called)
                # The reward should have been calculated in query_callback before this is called
                if incremental_rewards and len(incremental_rewards) > 0:
                    reward = incremental_rewards[-1]
                    if reward > 0:
                        reward_color = Colors.REWARD_POSITIVE
                        reward_sign = "+"
                    elif reward < 0:
                        reward_color = Colors.REWARD_NEGATIVE
                        reward_sign = ""
                    else:
                        reward_color = Colors.REWARD_NEUTRAL
                        reward_sign = ""
                    
                    reward_str = f"{reward_sign}{reward:.2f}"
                    print(colorize(f"Reward: {reward_str}", reward_color + Colors.BOLD))
                    total_color = Colors.REWARD_POSITIVE if total_incremental_reward > 0 else (Colors.REWARD_NEGATIVE if total_incremental_reward < 0 else Colors.REWARD_NEUTRAL)
                    print(f"Total reward so far: {colorize(f'{total_incremental_reward:.2f}', total_color + Colors.BOLD)}\n")
                else:
                    # This shouldn't happen, but print something if it does
                    print(colorize("Reward: 0.00 (not calculated)", Colors.REWARD_NEUTRAL) + "\n")
        
        # Run agent investigation
        investigation_result = self.agent.investigate(
            query_callback=query_callback,
            verbose=verbose,
            query_print_callback=query_print_callback if verbose else None
        )
        
        # Ensure output is flushed
        if verbose:
            import sys
            sys.stdout.flush()
        
        # Print final report if verbose
        if verbose:
            print(colorize("="*60, Colors.REPORT))
            print(colorize("WATSON REPORT", Colors.REPORT + Colors.BOLD))
            print(colorize("="*60, Colors.REPORT))
            final_summary = investigation_result.get("final_summary", "")
            if final_summary:
                print(f"\n{colorize(final_summary, Colors.REPORT)}\n")
            else:
                print("\nNo final summary provided.\n")
        
        # Calculate final reward
        if verbose:
            print(colorize("="*60, Colors.HEADER))
            print(colorize("CALCULATING FINAL REWARD...", Colors.HEADER + Colors.BOLD))
            print(colorize("="*60, Colors.HEADER) + "\n")
        
        reward_result = self.reward_llm.calculate_reward(
            scenario=scenario,
            agent_investigation=investigation_result,
            tool_calls_made=investigation_result["tool_calls_made"]
        )
        
        # Add incremental reward total to result
        reward_result["incremental_reward_total"] = total_incremental_reward
        
        # Print reward breakdown if verbose
        if verbose:
            print(colorize("="*60, Colors.HEADER))
            print(colorize("FINAL REWARD BREAKDOWN", Colors.HEADER + Colors.BOLD))
            print(colorize("="*60, Colors.HEADER))
            print(f"\nAttack Detection: {reward_result.get('attack_detection', 0)}/10")
            print(f"Indicator Discovery: {reward_result.get('indicator_discovery', 0)}/10")
            print(f"Query Quality: {reward_result.get('query_quality', 0)}/10")
            print(f"Efficiency: {reward_result.get('efficiency', 0)}/10")
            print(f"Thoroughness: {reward_result.get('thoroughness', 0)}/10")
            print(f"\n{colorize('='*60, Colors.HEADER)}")
            total_final = reward_result.get('total_reward', 0)
            total_color = Colors.REWARD_POSITIVE if total_final >= 25 else Colors.REWARD_NEGATIVE if total_final < 15 else Colors.REWARD_NEUTRAL
            print(colorize(f"TOTAL REWARD: {total_final}/50", total_color + Colors.BOLD))
            print(f"{colorize('='*60, Colors.HEADER)}\n")
            
            # Show incremental reward summary
            inc_color = Colors.REWARD_POSITIVE if total_incremental_reward > 0 else Colors.REWARD_NEGATIVE if total_incremental_reward < 0 else Colors.REWARD_NEUTRAL
            print(f"Incremental reward total: {colorize(f'{total_incremental_reward:.2f}', inc_color + Colors.BOLD)}\n")
            
            if 'reasoning' in reward_result:
                print(f"Reasoning: {reward_result['reasoning']}\n")
        
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

