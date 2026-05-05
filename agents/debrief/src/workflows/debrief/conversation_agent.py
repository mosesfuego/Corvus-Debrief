"""Debrief conversation agent.

This is the LLM-facing narrator for the debrief workflow. Domain agents do the
manufacturing analysis; this layer gathers tool output and writes the final
human-readable debrief.
"""

import json
from openai import OpenAI
from workflows.debrief.tools import (
    get_build_metrics,
    get_bottleneck_report,
    get_at_risk_report,
    flag_for_team,
)
from memory.memory import get_recent_context
from pathlib import Path

_THIS_FILE = Path(__file__).resolve()
_SRC_DIR = _THIS_FILE.parents[2]
_AGENT_ROOT = _THIS_FILE.parents[3]

_PROJECT_ROOT = _AGENT_ROOT.parent.parent

PROMPT_PATH = _AGENT_ROOT / "prompts" / "system_prompt.txt"

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
def _extended_nonempty(k: str, v) -> bool:
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    return True


def trim_tool_result(result, max_builds: int = 10):
    """
    Cap list length for tool results. Drop empty extended field values.
    """
    if not isinstance(result, list):
        return result

    trimmed = [dict(b) for b in result[:max_builds]]
    for build in trimmed:
        ext = build.get("extended")
        if isinstance(ext, dict):
            build["extended"] = {
                k: v for k, v in ext.items()
                if _extended_nonempty(k, v)
            }
    return trimmed

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


def run_deterministic_demo_debrief(config: dict, onboarding: dict) -> str:
    """
    Local demo fallback for zero-setup runs.
    Used only when --demo is selected and no LLM API key is available.
    """
    bundle = get_build_metrics(config, onboarding)
    signals = bundle["signals"]
    summary = bundle["summary"]

    for build in signals["blocked"]:
        team = (
            "Quality Assurance"
            if "broker" in build.get("notes", "").lower()
            else "Production"
        )
        flag_for_team(
            build_id=build["build_id"],
            team=team,
            reason=build.get("notes", "Blocked work order requires action"),
            urgency="critical",
            config=config,
        )

    for build in signals["unassigned"]:
        flag_for_team(
            build_id=build["build_id"],
            team="Scheduling",
            reason="Work order has no assigned operator",
            urgency="high",
            config=config,
        )

    blocked_text = "; ".join(
        f"{b['build_id']} at {b['station_id']} ({b.get('notes', 'blocked')})"
        for b in signals["blocked"]
    ) or "None."
    at_risk_text = "; ".join(
        f"{b['build_id']} at {b['station_id']} is at risk"
        for b in signals["at_risk"]
    ) or "None."
    needs_decision_text = "; ".join(
        f"{b['build_id']} at {b['station_id']}"
        for b in signals["needs_decision"]
    ) or "None."

    return f"""SUMMARY
The floor has {summary['blocked_count']} blocked work orders and {summary['at_risk_count']} at-risk work orders. Tier 1 aerospace work is stopped by a feeder mismatch, an expired operator certification, and a broker buy QA hold. Scheduling also needs to cover an unassigned quick-turn SMT job before it becomes the next bottleneck.

PRIORITY FINDINGS
🔴 Blocked: {blocked_text}
🟡 At Risk: {at_risk_text}
🔵 Needs Decision: {needs_decision_text}
⚪ Pattern Note: ERR_FEED_MISMATCH on SMT_SIPLACE_B is paired with an expired operator certification, which points to a process and readiness issue rather than a one-off machine fault.

RECOMMENDED ACTIONS
- Clear feeder position 22 and recertify the Aero Medical operator before restarting ACS-2241 → Production
- Review broker buy substitution for C0402-100V and release or reject ACS-2198 → Quality Assurance
- Assign an operator to ACS-7740 before the quick-turn window closes → Scheduling"""


def run_debrief_agent(config: dict, onboarding: dict) -> str:
    """
    Main agent loop.
    think → tool → observe → think → recommend
    Returns final debrief string.
    """
    agent_config = config.get("agents", {})

    if not agent_config.get("api_key"):
        if config.get("_demo"):
            print("[CORVUS] No LLM API key found — using built-in demo reasoning.\n")
            return run_deterministic_demo_debrief(config, onboarding)
        raise EnvironmentError(
            "Missing LLM API key. Set NIM_API_KEY or OPENAI_API_KEY."
        )

    client = OpenAI(
        api_key=agent_config["api_key"],
        base_url=agent_config.get("base_url")
    )
    model = agent_config.get("model", "moonshotai/kimi-k2.6")

    # build customer context from onboarding
    terminology = onboarding.get("terminology", {})
    teams = [t["name"] for t in onboarding.get("teams", [])]
    shifts = onboarding.get("shifts", [])
    company = onboarding.get("company", "the company")
    site = onboarding.get("site", "the plant")

    with open(PROMPT_PATH, "r") as f:
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
    recent_context = get_recent_context(lookback=5, config=config)
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
            max_tokens=8192,
            extra_body={"chat_template_kwargs": {"thinking": False}},
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
                trimmed = trim_tool_result(result)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(trimmed),
                })

        # model is done reasoning
        elif finish_reason == "stop":
            print("[CORVUS] Debrief complete.\n")

            # try content first
            final = message.content

            # kimi on NIM sometimes puts final output in reasoning_content
            if not final or not final.strip():
                reasoning = getattr(message, "reasoning_content", "") or ""
                # extract everything after the last tool reasoning
                # the actual response is usually at the end
                if reasoning.strip():
                    final = reasoning.strip()

            if not final or not final.strip():
                print("[CORVUS] Empty model text after tool use; check provider output.")
                final = "No debrief generated."

            return final

        # unexpected state
        else:
            print(f"[CORVUS] Unexpected finish reason: {finish_reason}")
            break
