"""Watson Agent - Main agent that performs multi-hop log searches."""

from typing import Any, Callable, Dict, Optional

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import tool

from src.utils.config import Config
from src.prompts.agent import get_agent_system_prompt
from src.utils.colors import Colors, colorize


class WatsonAgent:
    """
    Main agent that performs long-horizon, multi-hop searches to uncover attacks.
    Uses Agno for cleaner tool calling.
    """

    def __init__(
        self,
        max_tool_calls: int = 100,
        model_id: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize the agent.

        Args:
            max_tool_calls: Maximum number of tool calls allowed in a single episode
            model_id: Optional model ID (defaults to Config.AGENT_MODEL)
            api_key: Optional API key (defaults to Config.OPENROUTER_API_KEY)
            base_url: Optional base URL (defaults to Config.OPENROUTER_BASE_URL)
        """
        self.max_tool_calls = max_tool_calls
        self.tool_calls_made = 0
        self.conversation_history: list[Dict[str, Any]] = []
        self._query_callback: Optional[Callable[[str], str]] = None
        self._verbose = False
        self._query_print_callback: Optional[Callable[[str, Optional[str]], None]] = None

        # Store model configuration (can be overridden for VERL)
        self._model_id = model_id or Config.AGENT_MODEL
        self._api_key = api_key or Config.OPENROUTER_API_KEY
        self._base_url = base_url or Config.OPENROUTER_BASE_URL

    def _create_agent(self) -> Agent:
        """Create an Agno agent with tools."""
        # Create wrapper functions that can access instance variables
        query_callback = self._query_callback
        verbose = self._verbose
        query_print_callback = self._query_print_callback
        tool_calls_made_ref = [self.tool_calls_made]  # Use list to allow modification

        @tool
        def query_logs(query: str) -> str:
            """
            Run a natural language query against the logs.

            Args:
                query: The natural language query (e.g., 'Give me all logins for user X').
            """
            if not query_callback:
                return "Error: Query callback not set"

            query = query.strip()
            if not query:
                return "Error: Empty query provided"

            # Print query if verbose
            if verbose and query_print_callback:
                try:
                    query_print_callback(query, None)
                except Exception:
                    pass

            # Execute query via callback
            result = query_callback(query) or "[Empty response]"

            # Print result if verbose
            if verbose:
                if query_print_callback:
                    try:
                        query_print_callback(query, result)
                    except Exception:
                        # Fallback: direct print
                        preview = result[:200] + ("..." if len(result) > 200 else "")
                        if Colors:
                            print(
                                colorize("DB responded", Colors.RESPONSE + Colors.BOLD)
                                + f': "{colorize(preview, Colors.RESPONSE)}"'
                            )
                        else:
                            print(f'DB responded: "{preview}"')

            tool_calls_made_ref[0] += 1
            self.tool_calls_made = tool_calls_made_ref[0]
            return result

        @tool
        def finish_investigation(summary: str) -> str:
            """
            Signal that you have completed your investigation and have reconstructed the full attack timeline.

            Args:
                summary: Your final summary of the attack timeline and findings.
            """
            if verbose:
                print(
                    colorize(
                        "\nAgent finished investigation.\n",
                        Colors.REWARD_POSITIVE + Colors.BOLD,
                    )
                )
            return f"Investigation marked as complete: {summary}"

        # Create agent with tools
        agent = Agent(
            model=OpenAIChat(
                id=self._model_id,
                api_key=self._api_key,
                base_url=self._base_url,
            ),
            tools=[query_logs, finish_investigation],
            instructions=get_agent_system_prompt(),
            markdown=True,
        )

        return agent

    def investigate(
        self,
        query_callback: Callable[[str], str],
        initial_prompt: Optional[str] = None,
        verbose: bool = False,
        query_print_callback: Optional[Callable[[str, Optional[str]], None]] = None,
    ) -> Dict[str, Any]:
        """
        Perform an investigation by making multiple tool calls.

        Args:
            query_callback: Function to call when agent wants to query logs
            initial_prompt: Optional initial prompt to start the investigation
            verbose: Whether to print verbose output
            query_print_callback: Optional callback for printing queries/responses

        Returns:
            Dictionary containing the investigation results and conversation history
        """
        self.tool_calls_made = 0
        self.conversation_history = []
        self._query_callback = query_callback
        self._verbose = verbose
        self._query_print_callback = query_print_callback

        # Create agent
        agent = self._create_agent()

        # Run investigation
        prompt = initial_prompt or "Begin investigating the logs to uncover any security incidents."

        try:
            response = agent.run(prompt)

            # Extract conversation history from agent
            # Note: Agno handles tool calling internally, so we need to extract the history
            final_summary = response.content if hasattr(response, "content") else str(response)

            return {
                "tool_calls_made": self.tool_calls_made,
                "conversation_history": self.conversation_history,
                "final_summary": final_summary,
            }
        except Exception as e:
            if verbose:
                print(f"Error during investigation: {e}")
            return {
                "tool_calls_made": self.tool_calls_made,
                "conversation_history": self.conversation_history,
                "final_summary": "",
            }

    def reset(self):
        """Reset the agent state."""
        self.tool_calls_made = 0
        self.conversation_history = []
        self._query_callback = None
