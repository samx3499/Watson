"""Script to collect training data by running episodes."""
import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.scenarios import ATTACK_SCENARIOS, get_scenarios_by_difficulty
from src.episode import EpisodeRunner


def main():
    parser = argparse.ArgumentParser(description="Collect training data by running episodes")
    parser.add_argument(
        "--scenarios",
        type=str,
        nargs="+",
        help="Specific scenario IDs to run (default: all scenarios)",
    )
    parser.add_argument(
        "--max-difficulty",
        type=int,
        default=10,
        help="Maximum difficulty level (default: 10)",
    )
    parser.add_argument(
        "--episodes-per-scenario",
        type=int,
        default=1,
        help="Number of episodes to run per scenario (default: 1)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/episodes",
        help="Directory to save episode results (default: data/episodes)",
    )
    
    args = parser.parse_args()
    
    # Validate config
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please set OPENAI_API_KEY and OPENPIPE_API_KEY in your environment or .env file")
        sys.exit(1)
    
    # Select scenarios
    if args.scenarios:
        scenarios = [s for s in ATTACK_SCENARIOS if s.id in args.scenarios]
        if len(scenarios) != len(args.scenarios):
            print(f"Warning: Some scenario IDs not found")
    else:
        scenarios = get_scenarios_by_difficulty(args.max_difficulty)
    
    print(f"Running {len(scenarios)} scenario(s) with {args.episodes_per_scenario} episode(s) each")
    print(f"Total episodes: {len(scenarios) * args.episodes_per_scenario}")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run episodes
    runner = EpisodeRunner()
    all_results = []
    
    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"Scenario: {scenario.name} ({scenario.id})")
        print(f"Difficulty: {scenario.difficulty}")
        print(f"{'='*60}")
        
        for episode_num in range(args.episodes_per_scenario):
            print(f"\nEpisode {episode_num + 1}/{args.episodes_per_scenario}")
            
            try:
                result = runner.run_episode(scenario)
                all_results.append(result)
                
                # Save individual episode
                episode_file = output_dir / f"{scenario.id}_episode_{episode_num + 1}.json"
                with open(episode_file, "w") as f:
                    json.dump(result, f, indent=2)
                
                # Print summary
                reward = result["reward"]
                print(f"  Tool calls made: {result['investigation']['tool_calls_made']}")
                print(f"  Total reward: {reward.get('total_reward', 'N/A')}")
                print(f"  Attack detection: {reward.get('attack_detection', 'N/A')}")
                
            except Exception as e:
                print(f"  Error in episode: {e}")
                import traceback
                traceback.print_exc()
    
    # Save summary
    summary_file = output_dir / "summary.json"
    with open(summary_file, "w") as f:
        json.dump({
            "total_episodes": len(all_results),
            "scenarios_run": [s.id for s in scenarios],
            "results": all_results
        }, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Completed {len(all_results)} episodes")
    print(f"Results saved to {output_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

