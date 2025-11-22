"""Reward LLM prompts."""


def get_reward_evaluation_prompt(
    scenario_name: str,
    scenario_type: str,
    scenario_description: str,
    expected_indicators: list,
    conversation_summary: str,
    tool_calls_made: int
) -> str:
    """Get the reward evaluation prompt."""
    indicators_text = "\n".join(f"- {indicator}" for indicator in expected_indicators)
    
    return f"""You are evaluating a security analyst's investigation of a potential security incident.

ATTACK SCENARIO:
Name: {scenario_name}
Type: {scenario_type}
Description: {scenario_description}

EXPECTED INDICATORS (what the analyst should have discovered):
{indicators_text}

INVESTIGATION SUMMARY:
{conversation_summary}

TOOL CALLS MADE: {tool_calls_made}

Evaluate the investigation on the following criteria (each scored 0-10):

1. ATTACK DETECTION (0-10): Did the analyst identify the attack? How accurately?
2. INDICATOR DISCOVERY (0-10): How many expected indicators were discovered?
3. QUERY QUALITY (0-10): Were the queries well-formed and effective?
4. EFFICIENCY (0-10): Was the investigation efficient (fewer tool calls = better, but not at expense of thoroughness)?
5. THOROUGHNESS (0-10): Was the investigation comprehensive?

Provide your evaluation as a JSON object with this structure:
{{
    "attack_detection": <score 0-10>,
    "indicator_discovery": <score 0-10>,
    "query_quality": <score 0-10>,
    "efficiency": <score 0-10>,
    "thoroughness": <score 0-10>,
    "total_reward": <sum of all scores>,
    "reasoning": "<brief explanation of scores>"
}}

Be strict but fair. Reward good detective work and penalize missed attacks or inefficient queries.
"""


def get_reward_system_prompt() -> str:
    """Get the system prompt for reward evaluation."""
    return "You are an expert security analyst evaluating investigations. Provide detailed, fair evaluations."