"""Script to collect training data by running episodes."""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.scenarios import ATTACK_SCENARIOS, get_scenarios_by_difficulty

# NOTE: EpisodeRunner removed - will be replaced with Agent-lightning Trainer
# from src.episode import EpisodeRunner


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
            print("Warning: Some scenario IDs not found")
    else:
        scenarios = get_scenarios_by_difficulty(args.max_difficulty)

    print(f"Running {len(scenarios)} scenario(s) with {args.episodes_per_scenario} episode(s) each")
    print(f"Total episodes: {len(scenarios) * args.episodes_per_scenario}")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # NOTE: This script needs to be updated to use Agent-lightning Trainer
    # For now, it's disabled as EpisodeRunner has been removed
    print("\n" + "=" * 60)
    print("WARNING: This script needs to be updated for Agent-lightning")
    print("EpisodeRunner has been removed. Use Agent-lightning Trainer instead.")
    print("=" * 60)
    sys.exit(1)

    # TODO: Rewrite using Agent-lightning Trainer
    # Example:
    # from agentlightning import Trainer
    # trainer = Trainer(...)
    # trainer.fit(agent, train_dataset=scenarios, ...)

    # Save summary
    summary_file = output_dir / "summary.json"
    with open(summary_file, "w") as f:
        json.dump(
            {
                "total_episodes": len(all_results),
                "scenarios_run": [s.id for s in scenarios],
                "results": all_results,
            },
            f,
            indent=2,
        )

    print(f"\n{'=' * 60}")
    print(f"Completed {len(all_results)} episodes")
    print(f"Results saved to {output_dir}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
