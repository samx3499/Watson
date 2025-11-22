"""Example script demonstrating how to run a single episode."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.scenarios import get_scenario_by_id
from src.episode import EpisodeRunner


def main():
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nPlease create a .env file with:")
        print("  OPENROUTER_API_KEY=sk-or-v1-...")
        print("\nOptional:")
        print("  WANDB_API_KEY=your-wandb-key")
        print("  OPENPIPE_API_KEY=opk-...  # Only needed for cloud logging")
        return
    
    # Select a scenario
    scenario_id = "insider-threat-001"  # Change this to try different scenarios
    scenario = get_scenario_by_id(scenario_id)
    
    print("="*60)
    print("Watson Episode Runner")
    print("="*60)
    print(f"\nScenario: {scenario.name}")
    print(f"Type: {scenario.attack_type}")
    print(f"Difficulty: {scenario.difficulty}")
    print(f"\nDescription: {scenario.description}")
    print("\n" + "="*60)
    
    # Run episode
    runner = EpisodeRunner()
    print("\nRunning episode...\n")
    
    try:
        result = runner.run_episode(scenario)
        
        # Print results
        print("\n" + "="*60)
        print("Episode Results")
        print("="*60)
        print(f"\nTool calls made: {result['investigation']['tool_calls_made']}")
        
        reward = result['reward']
        print(f"\nReward Breakdown:")
        print(f"  Attack Detection: {reward.get('attack_detection', 'N/A')}/10")
        print(f"  Indicator Discovery: {reward.get('indicator_discovery', 'N/A')}/10")
        print(f"  Query Quality: {reward.get('query_quality', 'N/A')}/10")
        print(f"  Efficiency: {reward.get('efficiency', 'N/A')}/10")
        print(f"  Thoroughness: {reward.get('thoroughness', 'N/A')}/10")
        print(f"  Total Reward: {reward.get('total_reward', 'N/A')}/50")
        
        if 'reasoning' in reward:
            print(f"\nReasoning: {reward['reasoning']}")
        
        print(f"\nFinal Summary:")
        print(result['investigation'].get('final_summary', 'N/A'))
        
    except Exception as e:
        print(f"\nError running episode: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

