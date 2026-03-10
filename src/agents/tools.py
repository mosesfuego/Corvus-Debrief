"""
Corvus agent tools.
These are the functions the agent can call during its reasoning loop.
"""

from connectors.factory import get_connector
from analytics.build_metrics import BuildMetrics


def get_build_metrics(config: dict, onboarding: dict) -> list[dict]:
    """Fetch and evaluate all current builds."""
    connector = get_connector(config)
    analytics = BuildMetrics(config, onboarding)
    builds = connector.fetch_builds()
    return analytics.evaluate(builds)


def get_bottleneck_report(config: dict, onboarding: dict) -> list[dict]:
    """Returns only blocked work orders."""
    connector = get_connector(config)
    return connector.get_bottleneck_report()


def get_at_risk_report(config: dict, onboarding: dict) -> list[dict]:
    """Returns work orders that will miss their deadline."""
    connector = get_connector(config)
    return connector.get_at_risk_report()


def flag_for_team(
    build_id: str,
    team: str,
    reason: str,
    urgency: str = "normal"
) -> dict:
    """Routes a finding to a specific team."""
    flag = {
        "build_id": build_id,
        "team": team,
        "reason": reason,
        "urgency": urgency,
    }
    print(f"[CORVUS FLAG] → {team} | {urgency.upper()} | {build_id}: {reason}")
    return flag
