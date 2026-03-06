"""
Corvus agent tools.
These are the functions the agent can call during its reasoning loop.
Each tool returns clean, structured data the LLM can reason over.
"""

from connectors.factory import get_connector
from analytics.build_metrics import BuildMetrics


def get_build_metrics(config: dict) -> list[dict]:
    """
    Fetch and evaluate all current builds.
    Returns enriched builds with duration, delay_flag, completion_pct.
    """
    connector = get_connector(config)
    analytics = BuildMetrics(config)
    builds = connector.fetch_builds()
    return analytics.evaluate(builds)


def get_bottleneck_report(config: dict) -> list[dict]:
    """
    Returns only blocked work orders.
    Highest priority — something is completely stopped.
    """
    connector = get_connector(config)
    return connector.get_bottleneck_report()


def get_at_risk_report(config: dict) -> list[dict]:
    """
    Returns work orders where planned_end exceeds needed_by_date.
    These will miss their deadline if nothing changes.
    """
    connector = get_connector(config)
    return connector.get_at_risk_report()


def flag_for_team(
    build_id: str,
    team: str,
    reason: str,
    urgency: str = "normal"
) -> dict:
    """
    Routes a finding to a specific team.
    MVP — prints and returns structured flag.
    Phase 3 this becomes a real notification/checklist entry.
    """
    flag = {
        "build_id": build_id,
        "team": team,
        "reason": reason,
        "urgency": urgency,
    }

    print(f"[CORVUS FLAG] → {team} | {urgency.upper()} | {build_id}: {reason}")
    return flag
