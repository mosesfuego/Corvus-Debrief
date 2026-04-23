"""
Corvus agent tools.
These are the functions the agent can call during its reasoning loop.
"""

from connectors.factory import get_connector
from analytics.build_metrics import BuildMetrics


def get_build_metrics(config: dict, onboarding: dict) -> dict:
    """
    Fetch and evaluate all current builds.
    Returns structured analytics output:
      - builds: enriched build list
      - summary: counts and rates
      - signals: pre-computed, deterministic signal groups
    """
    connector = get_connector(config, onboarding)
    analytics = BuildMetrics(config, onboarding)
    builds = connector.fetch_builds()
    evaluated = analytics.evaluate(builds)

    # structured signal groups
    blocked   = [b for b in evaluated if b["signals"]["blocked"]]
    delayed   = [b for b in evaluated if b["signals"]["delayed"]]
    stalled   = [b for b in evaluated if b["signals"]["stalled"]]
    at_risk   = [b for b in evaluated if b["signals"]["at_risk"]]
    unassigned = [b for b in evaluated if b["signals"]["unassigned"]]
    needs_decision = [b for b in evaluated if b["signals"]["needs_decision"]]

    return {
        "builds": evaluated,
        "summary": {
            "total":           len(evaluated),
            "completed":       len([b for b in evaluated if b.get("status") == "Completed"]),
            "in_progress":     len([b for b in evaluated if b.get("status") == "In Progress"]),
            "blocked_count":   len(blocked),
            "at_risk_count":   len(at_risk),
            "unassigned_count": len(unassigned),
        },
        "signals": {
            "blocked":         [_build_summary(b) for b in blocked],
            "delayed":         [_build_summary(b) for b in delayed],
            "stalled":         [_build_summary(b) for b in stalled],
            "at_risk":         [_build_summary(b) for b in at_risk],
            "unassigned":      [_build_summary(b) for b in unassigned],
            "needs_decision":  [_build_summary(b) for b in needs_decision],
        }
    }


def _build_summary(build: dict) -> dict:
    """
    Compact build representation for signal groups.
    Keeps agent context window lean.
    """
    summary = {
        "build_id":      build.get("build_id", "UNKNOWN"),
        "station_id":    build.get("station_id", "UNKNOWN"),
        "status":        build.get("status", "UNKNOWN"),
        "completion_pct": build.get("completion_pct", 0.0),
        "duration_hours": build.get("duration_hours"),
        "operator_id":   build.get("operator_id", "UNKNOWN"),
        "notes":         build.get("notes", ""),
        "signals":       build.get("signals", {}),
    }
    # include extended fields if present
    if build.get("extended"):
        summary["extended"] = build["extended"]
    return summary


def get_bottleneck_report(config: dict, onboarding: dict) -> list[dict]:
    """Returns only blocked work orders."""
    connector = get_connector(config, onboarding)
    return connector.get_bottleneck_report()


def get_at_risk_report(config: dict, onboarding: dict) -> list[dict]:
    """Returns work orders that will miss their deadline."""
    connector = get_connector(config, onboarding)
    return connector.get_at_risk_report()


def flag_for_team(
    build_id: str,
    team: str,
    reason: str,
    urgency: str = "normal",
    config: dict = None
) -> dict:
    """Routes a finding to a specific team."""
    flag = {
        "build_id": build_id,
        "team":     team,
        "reason":   reason,
        "urgency":  urgency,
    }
    print(f"[CORVUS] Flag → {team} | {urgency.upper()} | {build_id}: {reason}")

    if config is not None:
        config.setdefault("_flags", []).append(flag)

    return flag
