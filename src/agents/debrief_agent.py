"""
Corvus debrief agent.
think → tool → observe → think loop.
Uses OpenAI-compatible client — works with Kimi K2 or any compatible provider.
"""

import json
from openai import OpenAI
from agents.tools import (
    get_build_metrics,
    get_bottleneck_report,
    get_at_risk_report,
    flag_for_team,
)
from memory.memory import get_recent_context, save_run


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_build_metrics",
            "description": "Fetch all current builds with computed metrics. Call this first to get a full picture of the factory floor.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_bottleneck_report",
            "description": "Returns only blocked work orders. Use this to identify what is completely stopped.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_at_risk_report",
            "description": "Returns work orders that will miss their deadline if nothing changes.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "flag_for_team",
            "description": "Route a finding to a specific team for action.",
            "parameters": {
                "type": "object",
                "properties": {
                    "build_id": {
                        "type": "string",
                        "description": "The work order ID being flagged"
                    },
                    "team": {
                        "type": "string",
                        "description": "Which team should handle this"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why this is being flagged"
                    },
                    "urgency": {
                        "type": "string",
                        "enum": ["normal", "high", "critical"]
                    }
                },
                "required": ["build_id", "team", "reason"]
            }
        }
    }
]


def dispatch_tool(
    tool_name: str,
    tool_input: dict,
    config: dict,
    onboarding: dict
):
    """Execute a tool by name and return its result."""
    if tool_name == "get_build_metrics":
        return get_build_metrics(config, onboarding)
    elif tool_name == "get_bottleneck_report":
        return get_bottleneck_report(config, onboarding)
    elif tool_name == "get_at_risk_report":
        return get_at_risk_report(config, onboarding)
    elif tool_name == "flag_for_team":
        return flag_for_team(
            build_id=tool_input["build_id"],
            team=tool_input["team"],
            reason=tool_input["reason"],
            urgency=tool_input.get("urgency", "normal"),
            config=config
        )
    else:
        return {"error": f"Unknown tool: {tool_name}"}


def run_debrief_agent(config: dict, onboarding: dict) -> str:
    """
    Main agent loop.
    think → tool → observe → think → recommend
    Returns final debrief string.
    """
    agent_config = config.get("agents", {})

    client = OpenAI(
        api_key=agent_config["api_key"],
        base_url=agent_config.get("base_url")
    )
    model = agent_config.get("model", "moonshotai/kimi-k2.5")

    # build customer context from onboarding
    terminology = onboarding.get("terminology", {})
    teams = [t["name"] for t in onboarding.get("teams", [])]
    shifts = onboarding.get("shifts", [])
    company = onboarding.get("company", "the company")
    site = onboarding.get("site", "the plant")

    # load system prompt
    with open("prompts/system_prompt.txt", "r") as f:
        system_prompt = f.read()

    # inject customer context
    system_prompt += f"""

---

CUSTOMER CONTEXT:
- Company: {company}, Site: {site}
- Terminology: use "{terminology.get('build', 'build')}" instead of "build", "{terminology.get('operator', 'operator')}" instead of "operator"
- Teams to route findings to: {', '.join(teams)}
- Shifts: {', '.join([f"{s['name']} ({s['start']}–{s['end']})" for s in shifts])}
"""

    # inject memory context
    recent_context = get_recent_context(lookback=5)
    system_prompt += f"\n\n---\n\n{recent_context}"

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": "Run a full debrief of the current factory floor. Use your tools to gather data before reasoning."
        }
    ]

    print("[CORVUS] Starting debrief...\n")

    while True:
        response = client.chat.completions.create(
            model=model,
            tools=TOOL_SCHEMAS,
            messages=messages,
            temperature=1.00,
            max_tokens=4096
        )

        message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        # model wants to call tools
        if finish_reason == "tool_calls" or message.tool_calls:
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            for tool_call in message.tool_calls:
                print(f"[CORVUS] Calling tool: {tool_call.function.name}")
                tool_input = json.loads(tool_call.function.arguments)
                result = dispatch_tool(
                    tool_call.function.name,
                    tool_input,
                    config,
                    onboarding
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

        # model is done reasoning
        elif finish_reason == "stop":
            print("[CORVUS] Debrief complete.\n")
            final = (
                message.content
                or getattr(message, "reasoning_content", None)
                or "No debrief generated."
            )

            # save run to memory
            save_run(
                flags=config.get("_flags", []),
                metrics=config.get("_metrics", [])
            )

            return final

        # unexpected state
        else:
            print(f"[CORVUS] Unexpected finish reason: {finish_reason}")
            break
