"""Lightweight schedule risk agent."""

from agent_runtime.base import DomainAgent
from agent_runtime.context import AgentContext, ensure_agent_context
from agent_runtime.result import AgentResult, Finding
from domain_agents.schedule.rules import SCHEDULE_OWNER


class ScheduleAgent(DomainAgent):
    """Detects schedule recovery needs from evaluated work orders."""

    name = "schedule"
    domain = "schedule"

    def evaluate(self, context: AgentContext | list[dict]) -> dict:
        agent_context = ensure_agent_context(context)
        findings = []
        at_risk_count = 0
        delayed_count = 0
        stalled_count = 0

        for build in agent_context.builds:
            signals = build.get("signals", {})
            build_id = build.get("build_id", "UNKNOWN")
            if signals.get("at_risk"):
                at_risk_count += 1
                findings.append(Finding(
                    domain=self.domain,
                    severity="high",
                    build_id=build_id,
                    title=f"{build_id} needs schedule recovery",
                    owner=SCHEDULE_OWNER,
                    reason="Work order is at risk against its needed date",
                    evidence=_evidence(build),
                    recommended_action="Review recovery options and update priority or due-date plan.",
                ))
            elif signals.get("delayed") or signals.get("stalled"):
                delayed_count += int(bool(signals.get("delayed")))
                stalled_count += int(bool(signals.get("stalled")))
                findings.append(Finding(
                    domain=self.domain,
                    severity="normal",
                    build_id=build_id,
                    title=f"{build_id} may affect the schedule",
                    owner=SCHEDULE_OWNER,
                    reason="Work order is delayed or stalled",
                    evidence=_evidence(build),
                    recommended_action="Confirm whether this affects today's dispatch plan.",
                ))

        result = AgentResult(
            domain=self.domain,
            summary={
                "finding_count": len(findings),
                "at_risk_count": at_risk_count,
                "delayed_count": delayed_count,
                "stalled_count": stalled_count,
            },
            findings=findings,
        )
        return result.to_dict()


def _evidence(build: dict) -> list[str]:
    evidence = [build.get("build_id", "UNKNOWN")]
    for field in ("station_id", "planned_end", "needed_by_date", "status"):
        if build.get(field):
            evidence.append(f"{field}: {build[field]}")
    return evidence

