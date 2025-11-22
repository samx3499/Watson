"""Environment LLM that simulates a database/log system."""
from typing import List, Dict, Any, Optional
from openpipe import OpenAI
from src.config import Config
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
                "HTTP-Referer": "https://github.com/yourusername/watson",
                "X-Title": "Watson Environment",
            },
            openpipe=openpipe_config if openpipe_config else None
        )
        self.conversation_history: List[Dict[str, str]] = []
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the environment LLM."""
        return f"""You are a database/log system that responds to human-readable search queries.

You have access to logs and databases that contain information about a potential security incident.

ATTACK SCENARIO KNOWLEDGE:
{self.scenario.environment_knowledge}

Your role:
1. Respond to queries as if you are querying a real database/log system
2. Return human-readable summaries of what the query would return
3. Only reveal information that would be accessible through the query
4. Be realistic - don't reveal everything at once, let the agent discover through multiple queries
5. Format responses as if they came from a database query (e.g., "Query returned 3 results: ...")

Example:
Query: "Show me all logins from unusual IP addresses"
Response: "Found 3 logins from unusual IPs:
- alice.smith@company.com from 203.0.113.45 at 2024-01-15 14:00:00 UTC
- bob.jones@company.com from 203.0.113.46 at 2024-01-15 14:05:00 UTC  
- carol.white@company.com from 203.0.113.47 at 2024-01-15 14:10:00 UTC"

Remember: You know the attack scenario details, but reveal them gradually through natural query responses.
"""
    
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
        messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ]
        
        # Add context if provided
        if context:
            messages.extend(context)
        
        # Add current query
        messages.append({
            "role": "user",
            "content": f"Query: {query_text}"
        })
        
        # Call LLM
        response = self.client.chat.completions.create(
            model=Config.ENVIRONMENT_MODEL,
            messages=messages,
            openpipe={
                "tags": {
                    "component": Config.ENVIRONMENT_TAG,
                    "scenario_id": self.scenario.id,
                    "scenario_type": self.scenario.attack_type,
                },
                "log_request": bool(Config.OPENPIPE_API_KEY),  # Only log if API key is set
            } if Config.OPENPIPE_API_KEY else None,
            temperature=0.3,  # Lower temperature for more consistent responses
        )
        
        result = response.choices[0].message.content
        
        # Update conversation history
        self.conversation_history.append({
            "role": "user",
            "content": query_text
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": result
        })
        
        return result
    
    def reset(self):
        """Reset the conversation history."""
        self.conversation_history = []

