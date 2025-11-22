"""Database Agent - Simulates a database/log system."""

from typing import Dict, List, Optional

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.utils.config import Config
from src.prompts.environment import get_environment_system_prompt
from src.scenarios import AttackScenario


class DatabaseAgent:
    """
    Simulates a database/log system using an LLM.
    This LLM knows about attack scenarios and responds to queries accordingly.
    """

    def __init__(self, scenario: AttackScenario):
        """
        Initialize the database agent with a specific attack scenario.

        Args:
            scenario: The attack scenario that this environment knows about
        """
        self.scenario = scenario
        self.conversation_history: List[Dict[str, str]] = []

        # Create Agno agent
        self.agent = Agent(
            model=OpenAIChat(
                id=Config.ENVIRONMENT_MODEL,
                api_key=Config.OPENROUTER_API_KEY,
                base_url=Config.OPENROUTER_BASE_URL,
                temperature=0.3,  # Lower temperature for more consistent responses
            ),
            instructions=get_environment_system_prompt(self.scenario.environment_knowledge),
            markdown=True,
        )

    def query(self, query_text: str, context: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Execute a human-readable query against the simulated database.

        Args:
            query_text: Human-readable query from the agent
            context: Optional conversation context from previous queries

        Returns:
            Human-readable summary of query results
        """
        # Build prompt with context if provided
        prompt = f"Query: {query_text}"
        if context:
            # Add context to prompt
            context_str = "\n".join(
                [
                    f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                    for msg in context[-5:]  # Last 5 messages for context
                ]
            )
            prompt = f"{context_str}\n\n{prompt}"

        # Call agent
        response = self.agent.run(prompt)
        result = response.content if hasattr(response, "content") else str(response)

        # Update conversation history
        self.conversation_history.append({"role": "user", "content": query_text})
        self.conversation_history.append({"role": "assistant", "content": result})

        return result

    def reset(self):
        """Reset the conversation history."""
        self.conversation_history = []
