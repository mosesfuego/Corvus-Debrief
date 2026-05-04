"""Lightweight materials and kitting signal extraction."""


MATERIAL_TERMS = (
    "material", "shortage", "kit", "kitting", "inventory", "part",
    "supplier", "receipt", "lot", "broker buy", "substitution",
)


class MaterialsLiteAgent:
    """Detects material readiness signals from work-order-like rows."""

    def evaluate(self, builds: list[dict]) -> dict:
        findings = []
        for build in builds:
            haystack = _combined_text(build)
            if not any(term in haystack for term in MATERIAL_TERMS):
                continue
            findings.append({
                "domain": "materials",
                "severity": _severity(haystack),
                "build_id": build.get("build_id", "UNKNOWN"),
                "owner": "Materials",
                "reason": build.get("notes") or "Material-related signal detected",
                "evidence": _evidence(build),
            })

        return {
            "domain": "materials",
            "summary": {"finding_count": len(findings)},
            "findings": findings,
        }


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
    for key in ("Part_Number", "Material", "Shortage_Qty", "Supplier"):
        if extended.get(key):
            evidence.append(f"{key}: {extended[key]}")
    return evidence

