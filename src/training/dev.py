"""Dev script to test agent manually without Trainer overhead."""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scenarios import ATTACK_SCENARIOS
from src.training.lit_agent import LitWatsonAgent
from src.utils.config import Config


# Mock Agent-Lightning classes for manual testing
@dataclass
class MockLLM:
    model: str
    
    def get_base_url(self, rollout_id: str, attempt_id: str) -> str:
        return Config.OPENROUTER_BASE_URL

@dataclass
class MockAttempt:
    attempt_id: str = "attempt_0"

@dataclass
class MockRollout:
    rollout_id: str = "rollout_0"
    attempt: MockAttempt = field(default_factory=MockAttempt)

class MockResources(dict):
    pass


def main():
    """Test agent manually with a simple OpenAI endpoint."""
    # Validate config
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        return

    # Get a test scenario
    if not ATTACK_SCENARIOS:
        print("No scenarios found!")
        return

    scenario = ATTACK_SCENARIOS[0]
    print(f"Testing with scenario: {scenario.name}")

    # Create agent
    agent = LitWatsonAgent(max_tool_calls=20)

    # Prepare task data
    task = {
        "id": scenario.id,
        "name": scenario.name,
        "description": scenario.description,
        "attack_type": scenario.attack_type,
        "environment_knowledge": scenario.environment_knowledge,
        "expected_indicators": scenario.expected_indicators,
        "difficulty": scenario.difficulty,
    }

    # Prepare mock resources
    resources = MockResources()
    resources["main_llm"] = MockLLM(model=Config.AGENT_MODEL)
    
    # Prepare mock rollout metadata
    rollout_meta = MockRollout()

    # Run manual rollout
    print("\nRunning manual rollout...")
    try:
        reward = agent.rollout(task, resources, rollout_meta)
        print(f"\nRollout completed. Reward: {reward}")
    except Exception as e:
        print(f"\nRollout failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
