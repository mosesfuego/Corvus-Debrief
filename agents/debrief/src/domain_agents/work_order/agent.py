"""Work-order domain agent."""

from agent_runtime.base import DomainAgent
from agent_runtime.context import AgentContext, ensure_agent_context
from agent_runtime.result import AgentResult, Finding
from analytics.build_metrics import BuildMetrics
from canonical.work_order import WorkOrder
from domain_agents.work_order.rules import DEFAULT_OWNER, UNASSIGNED_OWNER


class WorkOrderAgent(DomainAgent):
    """Owns work-order status, risk, and production readiness signals."""

    name = "work_order"
    domain = "work_order"

    def __init__(self, config: dict | None = None, onboarding: dict | None = None):
        self.config = config or {}
        self.onboarding = onboarding or {}
        self.analytics = BuildMetrics(self.config, self.onboarding)

    def normalize(self, builds: list[dict]) -> list[dict]:
        return [WorkOrder.from_raw(build).to_dict() for build in builds]

    def evaluate(self, context: AgentContext | list[dict]) -> dict:
        agent_context = ensure_agent_context(
            context,
            config=self.config,
            onboarding=self.onboarding,
        )
        normalized = self.normalize(agent_context.raw_builds or agent_context.builds)
        evaluated = self.analytics.evaluate(normalized)

        blocked = [b for b in evaluated if b["signals"]["blocked"]]
        delayed = [b for b in evaluated if b["signals"]["delayed"]]
        stalled = [b for b in evaluated if b["signals"]["stalled"]]
        at_risk = [b for b in evaluated if b["signals"]["at_risk"]]
        unassigned = [b for b in evaluated if b["signals"]["unassigned"]]
        needs_decision = [
            b for b in evaluated if b["signals"]["needs_decision"]
        ]

        result = AgentResult(
            domain=self.domain,
            builds=evaluated,
            summary={
                "total": len(evaluated),
                "completed": len([
                    b for b in evaluated if b.get("status") == "Completed"
                ]),
                "in_progress": len([
                    b for b in evaluated if b.get("status") == "In Progress"
                ]),
                "blocked_count": len(blocked),
                "at_risk_count": len(at_risk),
                "unassigned_count": len(unassigned),
            },
            signals={
                "blocked": [_build_summary(b) for b in blocked],
                "delayed": [_build_summary(b) for b in delayed],
                "stalled": [_build_summary(b) for b in stalled],
                "at_risk": [_build_summary(b) for b in at_risk],
                "unassigned": [_build_summary(b) for b in unassigned],
                "needs_decision": [_build_summary(b) for b in needs_decision],
            },
            findings=self._findings(blocked, at_risk, unassigned),
        )
        return result.to_dict()

    def _findings(
        self,
        blocked: list[dict],
        at_risk: list[dict],
        unassigned: list[dict],
    ) -> list[Finding]:
        findings = []
        for build in blocked:
            build_id = build.get("build_id", "UNKNOWN")
            findings.append(Finding(
                domain=self.domain,
                severity="critical",
                build_id=build_id,
                title=f"{build_id} is blocked",
                owner=DEFAULT_OWNER,
                reason=build.get("notes") or "Work order is blocked",
                evidence=[build_id],
                recommended_action="Assign an owner to clear the blocking condition.",
            ))
        for build in at_risk:
            if build in blocked:
                continue
            build_id = build.get("build_id", "UNKNOWN")
            findings.append(Finding(
                domain=self.domain,
                severity="high",
                build_id=build_id,
                title=f"{build_id} is at risk",
                owner=DEFAULT_OWNER,
                reason="Work order is at risk",
                evidence=[build_id],
                recommended_action="Review due date, station status, and recovery plan.",
            ))
        for build in unassigned:
            build_id = build.get("build_id", "UNKNOWN")
            findings.append(Finding(
                domain=self.domain,
                severity="high",
                build_id=build_id,
                title=f"{build_id} has no assigned operator",
                owner=UNASSIGNED_OWNER,
                reason="Work order has no assigned operator",
                evidence=[build_id],
                recommended_action="Assign coverage before the job becomes a bottleneck.",
            ))
        return findings


def _build_summary(build: dict) -> dict:
    summary = {
        "build_id": build.get("build_id", "UNKNOWN"),
        "station_id": build.get("station_id", "UNKNOWN"),
        "status": build.get("status", "UNKNOWN"),
        "completion_pct": build.get("completion_pct", 0.0),
        "duration_hours": build.get("duration_hours"),
        "operator_id": build.get("operator_id", "UNKNOWN"),
        "notes": build.get("notes", ""),
        "signals": build.get("signals", {}),
    }
    if build.get("extended"):
        summary["extended"] = build["extended"]
    return summary

