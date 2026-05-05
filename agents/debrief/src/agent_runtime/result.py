"""Result structures shared by Corvus domain agents."""

from dataclasses import dataclass, field
from typing import Any

from agent_runtime.confidence import confidence_from_evidence

SEVERITY_RANK = {
    "critical": 4,
    "high": 3,
    "normal": 2,
    "low": 1,
}


@dataclass
class Finding:
    """A single auditable issue or opportunity found by a domain agent."""

    domain: str
    severity: str
    reason: str
    owner: str
    evidence: list[str] = field(default_factory=list)
    build_id: str | None = None
    title: str | None = None
    recommended_action: str | None = None
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = {
            "domain": self.domain,
            "severity": self.severity,
            "owner": self.owner,
            "reason": self.reason,
            "evidence": self.evidence,
            "confidence": (
                self.confidence
                if self.confidence is not None
                else confidence_from_evidence(self.evidence)
            ),
        }
        if self.build_id:
            result["build_id"] = self.build_id
        if self.title:
            result["title"] = self.title
        if self.recommended_action:
            result["recommended_action"] = self.recommended_action
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class AgentResult:
    """Standard result envelope returned by every domain agent."""

    domain: str
    summary: dict[str, Any] = field(default_factory=dict)
    findings: list[Finding | dict[str, Any]] = field(default_factory=list)
    signals: dict[str, Any] = field(default_factory=dict)
    missing_context: list[str] = field(default_factory=list)
    next_questions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    builds: list[dict[str, Any]] | None = None

    def to_dict(self, include_builds: bool = True) -> dict[str, Any]:
        result = {
            "domain": self.domain,
            "summary": self.summary,
            "findings": [
                f.to_dict() if isinstance(f, Finding) else f
                for f in self.findings
            ],
            "missing_context": self.missing_context,
            "next_questions": self.next_questions,
        }
        if self.signals:
            result["signals"] = self.signals
        if self.metadata:
            result["metadata"] = self.metadata
        if include_builds and self.builds is not None:
            result["builds"] = self.builds
        return result


def sort_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort findings by severity, confidence, then stable domain name."""
    return sorted(
        findings,
        key=lambda finding: (
            SEVERITY_RANK.get(finding.get("severity", "low"), 0),
            finding.get("confidence", 0),
            finding.get("domain", ""),
        ),
        reverse=True,
    )

