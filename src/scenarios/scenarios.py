"""Attack scenario definitions for Watson training."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml


@dataclass
class AttackScenario:
    """Represents an attack scenario for training."""

    id: str
    name: str
    description: str
    attack_type: str
    # Knowledge that the environment LLM should have about this attack
    environment_knowledge: str
    # Expected indicators that the agent should discover
    expected_indicators: List[str]
    # Difficulty level (1-10)
    difficulty: int


def _load_scenario_from_yaml(yaml_path: Path) -> AttackScenario:
    """Load a scenario from a YAML file."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scenario_data = data["scenario"]
    ground_truth = data.get("ground_truth", {})

    # Extract environment knowledge from ground_truth
    environment_knowledge_parts = []
    
    # Add company background if available
    if "company_background" in data:
        environment_knowledge_parts.append(f"Company Background:\n{data['company_background']}")
    
    if "what_happened" in ground_truth:
        environment_knowledge_parts.append(f"What happened:\n{ground_truth['what_happened']}")
    if "attack_method" in ground_truth:
        environment_knowledge_parts.append(f"Attack method:\n{ground_truth['attack_method']}")
    
    # Add detailed artifacts for environment knowledge
    if "indicators_of_compromise" in ground_truth:
        iocs = ground_truth["indicators_of_compromise"]
        if isinstance(iocs, dict) and "suspicious_windows_artifacts" in iocs:
            environment_knowledge_parts.append(
                f"Suspicious artifacts:\n{iocs['suspicious_windows_artifacts']}"
            )
        elif isinstance(iocs, list):
            # For list format, include them as indicators
            environment_knowledge_parts.append(f"Key indicators:\n{chr(10).join(f'- {ioc}' for ioc in iocs)}")

    environment_knowledge = "\n\n".join(environment_knowledge_parts) if environment_knowledge_parts else scenario_data.get("name", "")

    # Extract expected indicators
    expected_indicators = []
    if "indicators_of_compromise" in ground_truth:
        iocs = ground_truth["indicators_of_compromise"]
        if isinstance(iocs, list):
            # Direct list of indicators
            expected_indicators = iocs
        elif isinstance(iocs, dict):
            # Check if there's a list at the top level
            if "suspicious_windows_artifacts" in iocs:
                # Extract key indicators from the text description
                artifacts_text = iocs["suspicious_windows_artifacts"]
                # Look for common patterns and extract key phrases
                lines = artifacts_text.split("\n")
                for line in lines:
                    line = line.strip()
                    if line and (
                        "SUSPICIOUS" in line
                        or "Event ID" in line
                        or "MFT" in line
                        or "USN" in line
                        or "Registry" in line
                        or "Browser" in line
                    ):
                        # Extract meaningful indicators
                        if len(line) > 20 and len(line) < 200:  # Reasonable length
                            expected_indicators.append(line)
            # Also check for any list values in the dict
            for key, value in iocs.items():
                if isinstance(value, list):
                    expected_indicators.extend(value)

    # Fallback: use attack type and name as indicators if none found
    if not expected_indicators:
        expected_indicators = [
            f"{scenario_data['attack_type']} attack detected",
            f"Attack: {scenario_data['name']}",
        ]

    # Build description from ground_truth if available
    description = scenario_data.get("description", "")
    if not description and "what_happened" in ground_truth:
        description = ground_truth["what_happened"][:500] + "..." if len(ground_truth["what_happened"]) > 500 else ground_truth["what_happened"]

    return AttackScenario(
        id=scenario_data["id"],
        name=scenario_data["name"],
        description=description or scenario_data.get("name", ""),
        attack_type=scenario_data["attack_type"],
        environment_knowledge=environment_knowledge,
        expected_indicators=expected_indicators[:10],  # Limit to first 10
        difficulty=scenario_data.get("difficulty", 5),
    )


def _load_all_scenarios() -> List[AttackScenario]:
    """Load all scenarios from YAML files in the scenarios directory."""
    scenarios_dir = Path(__file__).parent
    scenarios = []

    # Load YAML files
    for yaml_file in scenarios_dir.glob("*.yaml"):
        if yaml_file.name.startswith("."):
            continue
        try:
            scenario = _load_scenario_from_yaml(yaml_file)
            scenarios.append(scenario)
        except Exception as e:
            print(f"Warning: Failed to load scenario from {yaml_file}: {e}")
            continue

    return scenarios


# Load scenarios on import
ATTACK_SCENARIOS: List[AttackScenario] = _load_all_scenarios()


def get_scenario_by_id(scenario_id: str) -> AttackScenario:
    """Get an attack scenario by its ID."""
    for scenario in ATTACK_SCENARIOS:
        if scenario.id == scenario_id:
            return scenario
    raise ValueError(f"Scenario {scenario_id} not found")


def get_scenarios_by_difficulty(max_difficulty: int) -> List[AttackScenario]:
    """Get all scenarios with difficulty <= max_difficulty."""
    return [s for s in ATTACK_SCENARIOS if s.difficulty <= max_difficulty]
