"""Canonical quality issue record."""

from dataclasses import dataclass, field


@dataclass
class QualityIssue:
    issue_id: str = "UNKNOWN"
    work_order_id: str = "UNKNOWN"
    issue_type: str = "quality"
    status: str = "Unknown"
    severity: str = "normal"
    defect_code: str | None = None
    owner: str | None = None
    notes: str = ""
    extended: dict = field(default_factory=dict)

    @classmethod
    def from_raw(cls, row: dict) -> "QualityIssue":
        return cls(
            issue_id=row.get("issue_id") or row.get("ncr_id") or row.get("id") or "UNKNOWN",
            work_order_id=row.get("work_order_id") or row.get("build_id") or "UNKNOWN",
            issue_type=row.get("issue_type") or "quality",
            status=row.get("status") or "Unknown",
            severity=row.get("severity") or "normal",
            defect_code=row.get("defect_code") or row.get("failure_code"),
            owner=row.get("owner"),
            notes=row.get("notes") or row.get("comments") or "",
            extended=row.get("extended") or {},
        )

