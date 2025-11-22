"""Training script for Watson agent using Agent-lightning and VERL."""

import os
from typing import Any, Dict, List

# CRITICAL: Delete VERL_MODEL_PATH from environment entirely
# We use hardcoded model path to avoid path issues
if "VERL_MODEL_PATH" in os.environ:
    bad_path = os.environ.pop("VERL_MODEL_PATH")
    print(f"[Init] Removed VERL_MODEL_PATH from environment: {bad_path}", flush=True)
    print(f"[Init] Using hardcoded model instead", flush=True)

import agentlightning as agl

from src.scenarios import get_scenarios_by_difficulty
from src.training.lit_agent import LitWatsonAgent
from src.utils.config import Config


def prepare_dataset(scenarios: List) -> List[Dict[str, Any]]:
    """Convert scenarios to training dataset format - pass YAML content as string."""
    from pathlib import Path

    import yaml

    scenarios_dir = Path(__file__).parent.parent / "scenarios"
    dataset = []

    # Load all YAML files and match by scenario ID
    yaml_files = {}
    for yaml_path in scenarios_dir.glob("*.yaml"):
        if yaml_path.name.startswith("."):
            continue
        try:
            with open(yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                scenario_id = data.get("scenario", {}).get("id")
                if scenario_id:
                    yaml_files[scenario_id] = yaml_path
        except Exception as e:
            print(f"Warning: Failed to read {yaml_path}: {e}")
            continue

    for scenario in scenarios:
        # Find the YAML file for this scenario by ID
        yaml_file = yaml_files.get(scenario.id)

        if yaml_file and yaml_file.exists():
            # Read the entire YAML file as a string
            with open(yaml_file, encoding="utf-8") as f:
                yaml_content = f.read()
            dataset.append({"scenario_yaml": yaml_content})
        else:
            # Fallback: use scenario data as dict (shouldn't happen)
            print(f"Warning: Could not find YAML file for scenario {scenario.id}")
            dataset.append({
                "scenario_yaml": f"id: {scenario.id}\nname: {scenario.name}\ndescription: {scenario.description}"
            })

    return dataset


def get_verl_config() -> Dict[str, Any]:
    """Get VERL configuration for training."""
    # HARDCODED model path to avoid environment variable issues
    model_path = "microsoft/Phi-3-mini-4k-instruct"
    print(f"Using HARDCODED model path: {model_path}")
    
    return {
        "model": {
            "model_path": model_path,
            "trust_remote_code": True,
        },
        "env": {
            "n_envs": 8,  # Number of parallel environments
            "n_steps": 32,  # Steps per update
        },
        "ppo": {
            "learning_rate": 1e-5,
            "batch_size": 64,
            "mini_batch_size": 16,
            "n_epochs": 4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "clip_range": 0.2,
            "entropy_coef": 0.01,
            "value_coef": 0.5,
        },
        "train": {
            "total_epochs": 2,
            "save_freq": 64,
        },
    }


def main():
    """Main training function."""
    # Validate config
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please set OPENROUTER_API_KEY in your environment or .env file")
        return

    # Prepare datasets
    train_scenarios = get_scenarios_by_difficulty(max_difficulty=10)
    val_scenarios = train_scenarios[: min(5, len(train_scenarios))]  # Use first 5 for validation

    train_data = prepare_dataset(train_scenarios)
    val_data = prepare_dataset(val_scenarios)

    print(f"Training on {len(train_data)} scenarios")
    print(f"Validating on {len(val_data)} scenarios")

    # Create agent
    agent = LitWatsonAgent(max_tool_calls=100)

    # Get VERL config
    verl_config = get_verl_config()

    # Create VERL algorithm
    algorithm = agl.VERL(verl_config)

    # Create trainer
    trainer = agl.Trainer(
        n_runners=4,  # Number of parallel runners
        algorithm=algorithm,
        adapter={"agent_match": None},  # Match all agent spans for training
    )

    # Train
    print("\nStarting training...")
    trainer.fit(
        agent=agent,
        train_dataset=train_data,
        val_dataset=val_data,
    )

    print("\nTraining completed!")


if __name__ == "__main__":
    main()
