"""Main Agent LLM that performs multi-hop log searches."""
from typing import List, Dict, Any, Optional, Callable
from openpipe import OpenAI
from src.config import Config


class AgentLLM:
    """
    Main agent that performs long-horizon, multi-hop searches to uncover attacks.
    Uses tool calls to interact with the environment.
    """
    
    def __init__(self, max_tool_calls: int = 100):
        """
        Initialize the agent.
        
        Args:
            max_tool_calls: Maximum number of tool calls allowed in a single episode
        """
        # Use OpenRouter (OpenAI-compatible) with optional OpenPipe logging
        openpipe_config = {}
        if Config.OPENPIPE_API_KEY:
            openpipe_config = {
                "api_key": Config.OPENPIPE_API_KEY,
                "base_url": Config.OPENPIPE_BASE_URL,
            }
        
        self.client = OpenAI(
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": "https://github.com/yourusername/watson",  # Optional
                "X-Title": "Watson RL Agent",  # Optional
            },
            openpipe=openpipe_config if openpipe_config else None
        )
        self.max_tool_calls = max_tool_calls
        self.tool_calls_made = 0
        self.conversation_history: List[Dict[str, Any]] = []
        
    def _build_system_prompt(self, scenario_description: str) -> str:
        """Build the system prompt for the agent."""
        return f"""You are a security analyst investigating potential security incidents in log data.

SCENARIO CONTEXT:
{scenario_description}

Your goal is to uncover security attacks by performing systematic log searches. You have access to a database/log system that responds to human-readable queries.

TOOLS AVAILABLE:
- query_logs: Execute a human-readable query against the log database
  Example queries:
    - "Show me all failed login attempts in the last 24 hours"
    - "Group logins by country and show the rarest ones"
    - "Find all users who accessed sensitive databases outside normal hours"
    - "Show me all outbound connections to external IPs in the last hour"

INSTRUCTIONS:
1. Start with broad queries to understand the data
2. Refine your queries based on results
3. Look for anomalies, patterns, and suspicious activities
4. Chain multiple queries together to build a complete picture
5. You can make up to {self.max_tool_calls} queries
6. When you've identified an attack or exhausted your queries, summarize your findings

Think step by step and be thorough in your investigation.
"""
    
    def _get_tools(self) -> List[Dict[str, Any]]:
        """Define the tools available to the agent."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_logs",
                    "description": "Execute a human-readable query against the log database. Use this to search logs, filter data, aggregate results, and discover patterns.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "A human-readable query describing what you want to search for in the logs. Be specific and clear."
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    
    def investigate(
        self,
        scenario_description: str,
        query_callback: Callable[[str], str],
        initial_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform an investigation by making multiple tool calls.
        
        Args:
            scenario_description: Description of the scenario to investigate
            query_callback: Function to call when agent wants to query logs
            initial_prompt: Optional initial prompt to start the investigation
            
        Returns:
            Dictionary containing the investigation results and conversation history
        """
        self.tool_calls_made = 0
        self.conversation_history = []
        
        # Build initial messages
        messages = [
            {"role": "system", "content": self._build_system_prompt(scenario_description)}
        ]
        
        if initial_prompt:
            messages.append({"role": "user", "content": initial_prompt})
        else:
            messages.append({
                "role": "user",
                "content": "Begin investigating the logs to uncover any security incidents."
            })
        
        # Main interaction loop
        while self.tool_calls_made < self.max_tool_calls:
            # Call the agent
            response = self.client.chat.completions.create(
                model=Config.AGENT_MODEL,
                messages=messages,
                tools=self._get_tools(),
                tool_choice="auto",
                openpipe={
                    "tags": {
                        "component": Config.AGENT_TAG,
                        "episode": f"episode_{self.tool_calls_made}",
                    },
                    "log_request": bool(Config.OPENPIPE_API_KEY),  # Only log if API key is set
                } if Config.OPENPIPE_API_KEY else None,
                temperature=0.7,
            )
            
            message = response.choices[0].message
            
            # Convert message to dict format for messages list
            message_dict = {
                "role": message.role,
                "content": message.content,
            }
            if message.tool_calls:
                message_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            
            messages.append(message_dict)
            self.conversation_history.append(message_dict)
            
            # Check if agent wants to use tools
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call.function.name == "query_logs":
                        # Extract query
                        import json
                        args = json.loads(tool_call.function.arguments)
                        query = args.get("query", "")
                        
                        # Execute query via callback
                        query_result = query_callback(query)
                        
                        # Add tool result to messages
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": query_result
                        }
                        messages.append(tool_message)
                        
                        self.tool_calls_made += 1
                        
                        # Add to conversation history
                        self.conversation_history.append(tool_message)
            else:
                # Agent is done (no more tool calls)
                break
        
        # Get final summary if needed
        if self.tool_calls_made > 0:
            messages.append({
                "role": "user",
                "content": "Provide a final summary of your investigation findings."
            })
            
            final_response = self.client.chat.completions.create(
                model=Config.AGENT_MODEL,
                messages=messages,
                openpipe={
                    "tags": {
                        "component": Config.AGENT_TAG,
                        "episode": "final_summary",
                    },
                    "log_request": bool(Config.OPENPIPE_API_KEY),  # Only log if API key is set
                } if Config.OPENPIPE_API_KEY else None,
                temperature=0.7,
            )
            
            final_message = final_response.choices[0].message
            final_message_dict = {
                "role": final_message.role,
                "content": final_message.content,
            }
            self.conversation_history.append(final_message_dict)
        
        return {
            "tool_calls_made": self.tool_calls_made,
            "conversation_history": self.conversation_history,
            "final_summary": self.conversation_history[-1].get("content", "") if self.conversation_history else ""
        }
    
    def reset(self):
        """Reset the agent state."""
        self.tool_calls_made = 0
        self.conversation_history = []

