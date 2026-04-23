"""
Corvus memory module.
Persists a rolling run history at shared/memory/log.json (project-relative).
"""

import json
import os
from datetime import datetime

_THIS_FILE = os.path.abspath(__file__)
_SRC_DIR = os.path.dirname(os.path.dirname(_THIS_FILE))
_AGENT_ROOT = os.path.dirname(_SRC_DIR)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_AGENT_ROOT))
_SHARED_DIR = os.path.join(_PROJECT_ROOT, "shared")
_MEMORY_DIR = os.path.join(_SHARED_DIR, "memory")
MEMORY_PATH = os.path.join(_MEMORY_DIR, "log.json")


def load_memory() -> dict:
    """Load existing memory log."""
    if not os.path.exists(MEMORY_PATH):
        return {"runs": []}
    with open(MEMORY_PATH, "r") as f:
        return json.load(f)


def save_run(flags: list[dict], evaluated_builds: list[dict]):
    """
    Append current run to memory log.
    Called at end of every debrief.
    """
    memory = load_memory()

    blocked = [
        m for m in evaluated_builds
        if m.get("signals", {}).get("blocked")
    ]
    at_risk = [
        m for m in evaluated_builds
        if m.get("signals", {}).get("at_risk")
    ]

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
        "blocked_stations": [b.get("station_id", "") for b in blocked],
    }

    memory["runs"].append(run)
    memory["runs"] = memory["runs"][-30:]

    os.makedirs(_MEMORY_DIR, exist_ok=True)
    with open(MEMORY_PATH, "w") as f:
        json.dump(memory, f, indent=2)


def get_recent_context(lookback: int = 5) -> str:
    """
    Plain text summary of recent runs for the system prompt.
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
