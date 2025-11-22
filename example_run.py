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
    
    # Run episode (verbose=True prints all the flow)
    runner = EpisodeRunner()
    
    try:
        result = runner.run_episode(scenario, verbose=True)
        
        # Episode runner already prints everything, so we're done
        print(f"\nEpisode completed. Tool calls made: {result['investigation']['tool_calls_made']}")
        
    except Exception as e:
        print(f"\nError running episode: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

