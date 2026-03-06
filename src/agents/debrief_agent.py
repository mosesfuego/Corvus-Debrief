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


def dispatch_tool(tool_name: str, tool_input: dict, config: dict):
    """Execute a tool by name and return its result."""
    if tool_name == "get_build_metrics":
        return get_build_metrics(config)
    elif tool_name == "get_bottleneck_report":
        return get_bottleneck_report(config)
    elif tool_name == "get_at_risk_report":
        return get_at_risk_report(config)
    elif tool_name == "flag_for_team":
        return flag_for_team(
            build_id=tool_input["build_id"],
            team=tool_input["team"],
            reason=tool_input["reason"],
            urgency=tool_input.get("urgency", "normal")
        )
    else:
        return {"error": f"Unknown tool: {tool_name}"}


def run_debrief_agent(config: dict) -> str:
    """
    Main agent loop.
    Returns final debrief string.
    """
    agent_config = config.get("agents", {})

    client = OpenAI(
        api_key=agent_config["api_key"],
        base_url=agent_config.get("base_url")  # points to Kimi's endpoint
    )
    model = agent_config.get("model", "kimi-k2-5")

    with open("prompts/system_prompt.txt", "r") as f:
        system_prompt = f.read()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Run a full debrief of the current factory floor. Use your tools to gather data before reasoning."}
    ]

    print("[CORVUS] Starting debrief...\n")

    while True:
        response = client.chat.completions.create(
            model=model,
            tools=TOOL_SCHEMAS,
            messages=messages,
            temperature=0.6
        )

        message = response.choices[0].message

        # model wants to call a tool
        if message.tool_calls:
            messages.append(message)  # append assistant message with tool calls

            for tool_call in message.tool_calls:
                print(f"[CORVUS] Calling tool: {tool_call.function.name}")
                tool_input = json.loads(tool_call.function.arguments)
                result = dispatch_tool(tool_call.function.name, tool_input, config)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

        # model is done reasoning
        else:
            print("[CORVUS] Debrief complete.\n")
            return message.content
