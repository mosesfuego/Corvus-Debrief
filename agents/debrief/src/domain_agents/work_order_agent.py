"""Work order domain agent."""

from analytics.build_metrics import BuildMetrics
from canonical.work_order import WorkOrder


class WorkOrderAgent:
    """Owns work-order status, risk, and production readiness signals."""

    def __init__(self, config: dict, onboarding: dict):
        self.config = config
        self.onboarding = onboarding
        self.analytics = BuildMetrics(config, onboarding)

    def normalize(self, builds: list[dict]) -> list[dict]:
        return [WorkOrder.from_raw(build).to_dict() for build in builds]

    def evaluate(self, builds: list[dict]) -> dict:
        normalized = self.normalize(builds)
        evaluated = self.analytics.evaluate(normalized)

        blocked = [b for b in evaluated if b["signals"]["blocked"]]
        delayed = [b for b in evaluated if b["signals"]["delayed"]]
        stalled = [b for b in evaluated if b["signals"]["stalled"]]
        at_risk = [b for b in evaluated if b["signals"]["at_risk"]]
        unassigned = [b for b in evaluated if b["signals"]["unassigned"]]
        needs_decision = [
            b for b in evaluated if b["signals"]["needs_decision"]
        ]

        return {
            "domain": "work_order",
            "builds": evaluated,
            "summary": {
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
            "signals": {
                "blocked": [_build_summary(b) for b in blocked],
                "delayed": [_build_summary(b) for b in delayed],
                "stalled": [_build_summary(b) for b in stalled],
                "at_risk": [_build_summary(b) for b in at_risk],
                "unassigned": [_build_summary(b) for b in unassigned],
                "needs_decision": [_build_summary(b) for b in needs_decision],
            },
            "findings": self._findings(blocked, at_risk, unassigned),
        }

    def _findings(
        self,
        blocked: list[dict],
        at_risk: list[dict],
        unassigned: list[dict],
    ) -> list[dict]:
        findings = []
        for build in blocked:
            findings.append({
                "domain": "work_order",
                "severity": "critical",
                "build_id": build.get("build_id", "UNKNOWN"),
                "owner": "Production",
                "reason": build.get("notes") or "Work order is blocked",
                "evidence": [build.get("build_id", "UNKNOWN")],
            })
        for build in at_risk:
            if build in blocked:
                continue
            findings.append({
                "domain": "work_order",
                "severity": "high",
                "build_id": build.get("build_id", "UNKNOWN"),
                "owner": "Production",
                "reason": "Work order is at risk",
                "evidence": [build.get("build_id", "UNKNOWN")],
            })
        for build in unassigned:
            findings.append({
                "domain": "work_order",
                "severity": "high",
                "build_id": build.get("build_id", "UNKNOWN"),
                "owner": "Scheduling",
                "reason": "Work order has no assigned operator",
                "evidence": [build.get("build_id", "UNKNOWN")],
            })
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

