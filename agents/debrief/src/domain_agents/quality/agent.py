"""Lightweight quality signal extraction from work-order-like rows."""

from agent_runtime.base import DomainAgent
from agent_runtime.context import AgentContext, ensure_agent_context
from agent_runtime.result import AgentResult, Finding
from domain_agents.quality.rules import EVIDENCE_FIELDS, QUALITY_TERMS


class QualityAgent(DomainAgent):
    """Detects quality-related signals without needing a full QMS connector."""

    name = "quality"
    domain = "quality"

    def evaluate(self, context: AgentContext | list[dict]) -> dict:
        agent_context = ensure_agent_context(context)
        findings = []
        for build in agent_context.builds:
            haystack = _combined_text(build)
            if not any(term in haystack for term in QUALITY_TERMS):
                continue
            build_id = build.get("build_id", "UNKNOWN")
            findings.append(Finding(
                domain=self.domain,
                severity=_severity(haystack),
                build_id=build_id,
                title=f"{build_id} has a quality signal",
                owner="Quality Assurance",
                reason=build.get("notes") or "Quality-related signal detected",
                evidence=_evidence(build),
                recommended_action="Review QA disposition, inspection status, or containment needs.",
            ))

        result = AgentResult(
            domain=self.domain,
            summary={"finding_count": len(findings)},
            findings=findings,
        )
        return result.to_dict()


QualityLiteAgent = QualityAgent


def _combined_text(build: dict) -> str:
    parts = [str(build.get("notes", ""))]
    extended = build.get("extended") or {}
    parts.extend(str(v) for v in extended.values())
    parts.extend(str(k) for k in extended.keys())
    return " ".join(parts).lower()


def _severity(text: str) -> str:
    if any(term in text for term in ("hold", "ncr", "mrb", "fail", "scrap")):
        return "high"
    return "normal"


def _evidence(build: dict) -> list[str]:
    evidence = [build.get("build_id", "UNKNOWN")]
    extended = build.get("extended") or {}
    for key in EVIDENCE_FIELDS:
        if extended.get(key):
            evidence.append(f"{key}: {extended[key]}")
    return evidence

