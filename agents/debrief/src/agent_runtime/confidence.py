"""Confidence scoring helpers for domain-agent findings."""


def clamp_confidence(value: float) -> float:
    """Keep confidence values in a predictable 0.0-1.0 range."""
    return round(max(0.0, min(1.0, value)), 2)


def confidence_from_evidence(
    evidence: list[str],
    base: float = 0.55,
    step: float = 0.1,
) -> float:
    """Raise confidence as a finding gains concrete supporting evidence."""
    return clamp_confidence(base + (len(evidence) * step))

