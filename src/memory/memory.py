"""
Corvus memory module.
Simple external memory — persists findings across sessions.
No LLM required. Just reads and writes JSON.
"""

import json
import os
from datetime import datetime


MEMORY_PATH = "memory/log.json"


def load_memory() -> dict:
    """Load existing memory log."""
    if not os.path.exists(MEMORY_PATH):
        return {"runs": []}
    with open(MEMORY_PATH, "r") as f:
        return json.load(f)


def save_run(flags: list[dict], metrics: list[dict]):
    """
    Append current run to memory log.
    Called at end of every debrief.
    """
    memory = load_memory()

    blocked = [m for m in metrics if m.get("status") == "Blocked"]
    at_risk = [m for m in metrics if m.get("delay_flag")]

    run = {
        "timestamp": datetime.now().isoformat(),
        "blocked_count": len(blocked),
        "at_risk_count": len(at_risk),
        "flags": [
            {
                "build_id": f["build_id"],
                "team": f["team"],
                "urgency": f["urgency"],
                "reason": f["reason"]
            }
            for f in flags
        ],
        "blocked_stations": [b["station_id"] for b in blocked],
    }

    memory["runs"].append(run)

    # keep last 30 runs only — prevents unbounded growth
    memory["runs"] = memory["runs"][-30:]

    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    with open(MEMORY_PATH, "w") as f:
        json.dump(memory, f, indent=2)


def get_recent_context(lookback: int = 5) -> str:
    """
    Returns a plain text summary of recent runs.
    Injected into agent system prompt so Corvus can reference history.
    """
    memory = load_memory()
    runs = memory.get("runs", [])[-lookback:]

    if not runs:
        return "No previous runs on record."

    lines = ["RECENT HISTORY (last runs):"]
    for run in runs:
        ts = run["timestamp"][:16].replace("T", " ")
        blocked = run.get("blocked_count", 0)
        at_risk = run.get("at_risk_count", 0)
        stations = ", ".join(run.get("blocked_stations", [])) or "none"
        lines.append(
            f"  {ts} — blocked: {blocked}, at risk: {at_risk}, "
            f"blocked stations: {stations}"
        )

    return "\n".join(lines)
