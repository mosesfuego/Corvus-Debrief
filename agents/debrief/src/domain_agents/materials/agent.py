"""Lightweight materials and kitting signal extraction."""

from agent_runtime.base import DomainAgent
from agent_runtime.context import AgentContext, ensure_agent_context
from agent_runtime.result import AgentResult, Finding
from domain_agents.materials.rules import EVIDENCE_FIELDS, MATERIAL_TERMS


class MaterialsAgent(DomainAgent):
    """Detects material readiness signals from work-order-like rows."""

    name = "materials"
    domain = "materials"

    def evaluate(self, context: AgentContext | list[dict]) -> dict:
        agent_context = ensure_agent_context(context)
        findings = []
        for build in agent_context.builds:
            haystack = _combined_text(build)
            if not any(term in haystack for term in MATERIAL_TERMS):
                continue
            build_id = build.get("build_id", "UNKNOWN")
            findings.append(Finding(
                domain=self.domain,
                severity=_severity(haystack),
                build_id=build_id,
                title=f"{build_id} has a material readiness signal",
                owner="Materials",
                reason=build.get("notes") or "Material-related signal detected",
                evidence=_evidence(build),
                recommended_action="Review material availability, substitution status, or supplier follow-up.",
            ))

        result = AgentResult(
            domain=self.domain,
            summary={"finding_count": len(findings)},
            findings=findings,
        )
        return result.to_dict()


MaterialsLiteAgent = MaterialsAgent


def _combined_text(build: dict) -> str:
    parts = [str(build.get("notes", "")), str(build.get("station_id", ""))]
    extended = build.get("extended") or {}
    parts.extend(str(v) for v in extended.values())
    parts.extend(str(k) for k in extended.keys())
    return " ".join(parts).lower()


def _severity(text: str) -> str:
    if any(term in text for term in ("shortage", "hold", "missing", "broker")):
        return "high"
    return "normal"


def _evidence(build: dict) -> list[str]:
    evidence = [build.get("build_id", "UNKNOWN")]
    extended = build.get("extended") or {}
    for key in EVIDENCE_FIELDS:
        if extended.get(key):
            evidence.append(f"{key}: {extended[key]}")
    return evidence

