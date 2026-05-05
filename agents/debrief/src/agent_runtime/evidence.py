"""Evidence helpers for auditable manufacturing findings."""

from typing import Any


def field_evidence(
    record: dict[str, Any],
    *fields: str,
    fallback_id_field: str = "build_id",
) -> list[str]:
    """Return compact field evidence strings for a finding."""
    evidence = []
    record_id = record.get(fallback_id_field)
    if record_id:
        evidence.append(str(record_id))

    for field in fields:
        value = record.get(field)
        if value not in (None, ""):
            evidence.append(f"{field}: {value}")

    extended = record.get("extended") or {}
    for field in fields:
        value = extended.get(field)
        if value not in (None, ""):
            evidence.append(f"{field}: {value}")

    return evidence

