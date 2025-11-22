"""Environment LLM that simulates a database/log system."""

from typing import Dict, List, Optional

from openai import OpenAI

from src.config import Config
from src.prompts.environment import get_environment_system_prompt
from src.scenarios import AttackScenario


class EnvironmentLLM:
    """
    Simulates a database/log system using an LLM.
    This LLM knows about attack scenarios and responds to queries accordingly.
    """

    def __init__(self, scenario: AttackScenario):
        """
        Initialize the environment with a specific attack scenario.

        Args:
            scenario: The attack scenario that this environment knows about
        """
        self.scenario = scenario
        # Use OpenRouter (OpenAI-compatible API)
        self.client = OpenAI(
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": "https://github.com/yourusername/watson",
                "X-Title": "Watson Environment",
            },
        )
        self.conversation_history: List[Dict[str, str]] = []

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the environment LLM."""
        return get_environment_system_prompt(self.scenario.environment_knowledge)

    def query(self, query_text: str, context: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Execute a human-readable query against the simulated database.

        Args:
            query_text: Human-readable query from the agent
            context: Optional conversation context from previous queries

        Returns:
            Human-readable summary of query results
        """
        # Build messages
        messages = [{"role": "system", "content": self._build_system_prompt()}]

        # Add context if provided
        if context:
            messages.extend(context)

        # Add current query
        messages.append({"role": "user", "content": f"Query: {query_text}"})

        # Call LLM
        response = self.client.chat.completions.create(
            model=Config.ENVIRONMENT_MODEL,
            messages=messages,
            temperature=0.3,  # Lower temperature for more consistent responses
        )

        result = response.choices[0].message.content

        # Update conversation history
        self.conversation_history.append({"role": "user", "content": query_text})
        self.conversation_history.append({"role": "assistant", "content": result})

        return result

    def reset(self):
        """Reset the conversation history."""
        self.conversation_history = []
