"""Main Agent LLM that performs multi-hop log searches."""
import json
import sys
from typing import List, Dict, Any, Optional, Callable
from openpipe import OpenAI
from src.config import Config
from src.prompts.agent import (
    get_agent_system_prompt,
    get_agent_initial_prompt,
    get_agent_retry_prompt,
    get_agent_continue_prompt,
    get_agent_first_turn_prompt,
)

# Import colors at module level for fallback printing
try:
    from src.colors import Colors, colorize
except ImportError:
    Colors = None
    def colorize(text: str, color: str = "") -> str:  # type: ignore
        return text


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
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the agent."""
        return get_agent_system_prompt()
    
    def _get_tools(self) -> List[Dict[str, Any]]:
        """Define the tools available to the agent."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_logs",
                    "description": "Run a natural language query against the logs.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The natural language query (e.g., 'Give me all logins for user X')."
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "finish_investigation",
                    "description": "Signal that you have completed your investigation and have reconstructed the full attack timeline. Only call this when you have gathered enough evidence through multiple queries.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "Your final summary of the attack timeline and findings."
                            }
                        },
                        "required": ["summary"]
                    }
                }
            }
        ]
    
    def investigate(
        self,
        query_callback: Callable[[str], str],
        initial_prompt: Optional[str] = None,
        verbose: bool = False,
        query_print_callback: Optional[Callable[[str, str], None]] = None
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
        
        # Build initial messages
        messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ]
        
        if initial_prompt:
            messages.append({"role": "user", "content": initial_prompt})
        else:
            messages.append({"role": "user", "content": get_agent_initial_prompt()})
        
        # Main interaction loop
        consecutive_no_tool_calls = 0
        max_consecutive_no_tool_calls = 2
        final_summary_from_tool = None
        
        while self.tool_calls_made < self.max_tool_calls:
            # Force tool calling on first turn, then use auto
            if self.tool_calls_made == 0:
                tool_choice = {"type": "function", "function": {"name": "query_logs"}}
            else:
                tool_choice = "auto"
            
            # Call the agent
            response = self.client.chat.completions.create(
                model=Config.AGENT_MODEL,
                messages=messages,
                tools=self._get_tools(),
                tool_choice=tool_choice,
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
                "content": message.content or None,  # Handle None content when tool calls are present
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
                consecutive_no_tool_calls = 0  # Reset counter
                
                # Check for finish_investigation tool call first
                finish_called = False
                for tool_call in message.tool_calls:
                    if tool_call.function.name == "finish_investigation":
                        try:
                            args = json.loads(tool_call.function.arguments)
                            summary = args.get("summary", "")
                            final_summary_from_tool = summary
                            
                            # Add tool response message (required by API)
                            tool_message = {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": "Investigation marked as complete."
                            }
                            messages.append(tool_message)
                            
                            # Store in conversation history
                            self.conversation_history.append({
                                "role": "assistant",
                                "content": summary,
                                "tool_calls": [{
                                    "id": tool_call.id,
                                    "type": tool_call.type,
                                    "function": {
                                        "name": tool_call.function.name,
                                        "arguments": tool_call.function.arguments
                                    }
                                }]
                            })
                            self.conversation_history.append(tool_message)
                            
                            if verbose:
                                print(colorize("\nAgent finished investigation.\n", Colors.REWARD_POSITIVE + Colors.BOLD))
                            finish_called = True
                        except json.JSONDecodeError:
                            pass
                        break
                
                if finish_called:
                    break
                
                # Handle query_logs tool calls
                for tool_call in message.tool_calls:
                    if tool_call.function.name == "query_logs":
                        try:
                            args = json.loads(tool_call.function.arguments)
                            query = args.get("query", "").strip()
                            
                            if not query:
                                query_result = "Error: Empty query provided"
                            else:
                                # Print query if verbose
                                if verbose and query_print_callback:
                                    try:
                                        query_print_callback(query, None)
                                        sys.stdout.flush()
                                    except Exception:
                                        pass
                                
                                # Execute query via callback
                                query_result = query_callback(query) or "[Empty response]"
                                
                                # Print result if verbose
                                if verbose:
                                    if query_print_callback:
                                        try:
                                            query_print_callback(query, query_result)
                                            sys.stdout.flush()
                                        except Exception:
                                            # Fallback: direct print
                                            preview = query_result[:200] + ('...' if len(query_result) > 200 else '')
                                            if Colors:
                                                print(colorize("DB responded", Colors.RESPONSE + Colors.BOLD) + 
                                                      f": \"{colorize(preview, Colors.RESPONSE)}\"")
                                            else:
                                                print(f"DB responded: \"{preview}\"")
                                            sys.stdout.flush()
                        except json.JSONDecodeError as e:
                            query_result = f"Error: Invalid JSON in tool arguments: {str(e)}"
                        except Exception as e:
                            query_result = f"Error executing query: {str(e)}"
                        
                        # Add tool result to messages
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": query_result
                        }
                        messages.append(tool_message)
                        self.tool_calls_made += 1
                        self.conversation_history.append(tool_message)
            else:
                # Agent didn't make a tool call
                consecutive_no_tool_calls += 1
                
                # If agent outputs text describing a tool call, prompt it to use the tool
                if message.content and ("query" in (message.content or "").lower() or "call" in (message.content or "").lower()):
                    messages.append({"role": "user", "content": get_agent_retry_prompt()})
                    consecutive_no_tool_calls -= 1
                    continue
                
                # If too many consecutive failures, break
                if consecutive_no_tool_calls >= max_consecutive_no_tool_calls:
                    if verbose:
                        print(colorize("\nAgent stopped (no tool calls made).\n", Colors.REWARD_NEUTRAL))
                    break
                
                # Prompt agent to continue or finish
                if self.tool_calls_made > 0:
                    messages.append({"role": "user", "content": get_agent_continue_prompt()})
                else:
                    messages.append({"role": "user", "content": get_agent_first_turn_prompt()})
        
        # Get final summary if needed (only if we don't already have one from finish_investigation)
        final_summary = final_summary_from_tool
        if not final_summary and self.tool_calls_made > 0:
            # Check if last message has unresolved tool calls
            last_message = messages[-1] if messages else None
            has_unresolved_tool_calls = (
                last_message and 
                last_message.get("role") == "assistant" and 
                "tool_calls" in last_message
            )
            
            # Only ask for summary if there are no unresolved tool calls
            if not has_unresolved_tool_calls:
                messages.append({
                    "role": "user",
                    "content": "Provide a final summary of your investigation findings."
                })
                
                try:
                    final_response = self.client.chat.completions.create(
                        model=Config.AGENT_MODEL,
                        messages=messages,
                        openpipe={
                            "tags": {
                                "component": Config.AGENT_TAG,
                                "episode": "final_summary",
                            },
                            "log_request": bool(Config.OPENPIPE_API_KEY),
                        } if Config.OPENPIPE_API_KEY else None,
                        temperature=0.7,
                    )
                    
                    final_message = final_response.choices[0].message
                    final_summary = final_message.content or ""
                    if final_summary:
                        final_message_dict = {
                            "role": final_message.role,
                            "content": final_summary,
                        }
                        self.conversation_history.append(final_message_dict)
                except Exception as e:
                    # If we can't get a summary, use the last assistant message content
                    if verbose:
                        print(f"Warning: Could not get final summary: {e}")
                    final_summary = ""
        
        return {
            "tool_calls_made": self.tool_calls_made,
            "conversation_history": self.conversation_history,
            "final_summary": final_summary or (self.conversation_history[-1].get("content", "") if self.conversation_history else "")
        }
    
    def reset(self):
        """Reset the agent state."""
        self.tool_calls_made = 0
        self.conversation_history = []

