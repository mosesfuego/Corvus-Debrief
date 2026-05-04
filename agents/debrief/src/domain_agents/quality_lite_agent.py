"""Lightweight quality signal extraction from work-order-like rows."""


QUALITY_TERMS = (
    "qa", "quality", "inspection", "inspect", "defect", "failure", "fail",
    "ncr", "mrb", "rework", "scrap", "yield", "hold", "nonconformance",
)


class QualityLiteAgent:
    """Detects quality-related signals without needing a full QMS connector."""

    def evaluate(self, builds: list[dict]) -> dict:
        findings = []
        for build in builds:
            haystack = _combined_text(build)
            if not any(term in haystack for term in QUALITY_TERMS):
                continue
            findings.append({
                "domain": "quality",
                "severity": _severity(haystack),
                "build_id": build.get("build_id", "UNKNOWN"),
                "owner": "Quality Assurance",
                "reason": build.get("notes") or "Quality-related signal detected",
                "evidence": _evidence(build),
            })

        return {
            "domain": "quality",
            "summary": {"finding_count": len(findings)},
            "findings": findings,
        }


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
    for key in ("Error_Code", "Defect_Code", "Inspection_Result", "Yield_Rate"):
        if extended.get(key):
            evidence.append(f"{key}: {extended[key]}")
    return evidence

