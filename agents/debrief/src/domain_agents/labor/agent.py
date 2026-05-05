"""Lightweight labor and staffing agent."""

from agent_runtime.base import DomainAgent
from agent_runtime.context import AgentContext, ensure_agent_context
from agent_runtime.result import AgentResult, Finding
from domain_agents.labor.rules import LABOR_TERMS


class LaborAgent(DomainAgent):
    """Detects assignment, staffing, and certification readiness signals."""

    name = "labor"
    domain = "labor"

    def evaluate(self, context: AgentContext | list[dict]) -> dict:
        agent_context = ensure_agent_context(context)
        findings = []
        unassigned_count = 0
        certification_count = 0

        for build in agent_context.builds:
            signals = build.get("signals", {})
            haystack = _combined_text(build)
            build_id = build.get("build_id", "UNKNOWN")

            if signals.get("unassigned"):
                unassigned_count += 1
                findings.append(Finding(
                    domain=self.domain,
                    severity="high",
                    build_id=build_id,
                    title=f"{build_id} needs labor assignment",
                    owner="Scheduling",
                    reason="Work order has no assigned operator",
                    evidence=_evidence(build),
                    recommended_action="Assign qualified coverage before the job blocks flow.",
                ))
                continue

            if any(term in haystack for term in LABOR_TERMS):
                if "cert" in haystack or "qualified" in haystack:
                    certification_count += 1
                findings.append(Finding(
                    domain=self.domain,
                    severity=_severity(haystack),
                    build_id=build_id,
                    title=f"{build_id} has a labor readiness signal",
                    owner="Production",
                    reason=build.get("notes") or "Labor-related signal detected",
                    evidence=_evidence(build),
                    recommended_action="Confirm operator coverage and qualification readiness.",
                ))

        result = AgentResult(
            domain=self.domain,
            summary={
                "finding_count": len(findings),
                "unassigned_count": unassigned_count,
                "certification_count": certification_count,
            },
            findings=findings,
        )
        return result.to_dict()


def _combined_text(build: dict) -> str:
    parts = [str(build.get("notes", "")), str(build.get("operator_id", ""))]
    extended = build.get("extended") or {}
    parts.extend(str(v) for v in extended.values())
    parts.extend(str(k) for k in extended.keys())
    return " ".join(parts).lower()


def _severity(text: str) -> str:
    if any(term in text for term in ("expired", "unassigned", "missing")):
        return "high"
    return "normal"


def _evidence(build: dict) -> list[str]:
    evidence = [build.get("build_id", "UNKNOWN")]
    for field in ("operator_id", "station_id", "status", "notes"):
        if build.get(field):
            evidence.append(f"{field}: {build[field]}")
    return evidence

