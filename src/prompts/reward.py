"""Reward LLM prompts."""


def get_reward_evaluation_prompt(
    scenario_name: str,
    scenario_type: str,
    scenario_description: str,
    expected_indicators: list,
    conversation_summary: str,
    tool_calls_made: int,
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


def get_incremental_reward_prompt(
    scenario_name: str,
    scenario_type: str,
    scenario_description: str,
    expected_indicators: list,
    query: str,
    response: str,
    query_number: int,
) -> str:
    """Get the incremental reward evaluation prompt."""
    indicators_text = "\n".join(f"- {indicator}" for indicator in expected_indicators)

    return f"""You are evaluating a single step in a security investigation.

ATTACK SCENARIO:
Name: {scenario_name}
Type: {scenario_type}
Description: {scenario_description}

EXPECTED INDICATORS:
{indicators_text}

STEP TO EVALUATE:
Query #{query_number}: {query}
Response: {response}

Evaluate this specific query and response pair.
Did the query move the investigation forward? Did it reveal relevant information?
Is the query efficient and well-formed?

Score this step from -1.0 to +1.0 using 0.1 increments.

Scoring Rubric:
-1.0: Harmful/Counter-productive (e.g., syntax error, repeating failed query)
-0.5: Poor (e.g., irrelevant query, very broad query that failed)
0.0: Neutral (e.g., 'list_tables', establishing context, or no new info found)
+0.1 to +0.3: Slight Progress (e.g., confirmed a negative result that narrows scope, found broad but relevant info)
+0.4 to +0.6: Good Progress (e.g., found specific relevant logs, identified a user/IP of interest)
+0.7 to +0.9: Major Discovery (e.g., found key indicator, exploit artifact, or attacker IP)
+1.0: Critical Breakthrough (e.g., definitive proof of attack, 'smoking gun')

Be precise. Avoid defaulting to 0.0 or 0.5 unless it exactly fits the rubric.

Provide ONLY a JSON object:
{{
    "score": <float between -1.0 and 1.0>,
    "reasoning": "<brief explanation>"
}}
"""


def get_reward_system_prompt() -> str:
    """Get the system prompt for reward evaluation."""
    return "You are an expert security analyst evaluating investigations. Provide detailed, fair evaluations."
