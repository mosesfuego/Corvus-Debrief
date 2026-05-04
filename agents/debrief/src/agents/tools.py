"""
Corvus agent tools.
These are the functions the agent can call during its reasoning loop.
"""

from orchestration.debrief_orchestrator import DebriefOrchestrator
from connectors.factory import get_connector


def get_build_metrics(config: dict, onboarding: dict) -> dict:
    """
    Fetch and evaluate all current builds.
    Returns structured analytics output:
      - builds: enriched build list
      - summary: counts and rates
      - signals: pre-computed, deterministic signal groups
    """
    return DebriefOrchestrator(config, onboarding).build_context()


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
