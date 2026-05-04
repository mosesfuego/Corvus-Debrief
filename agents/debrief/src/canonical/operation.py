"""Canonical operation/routing step record."""

from dataclasses import dataclass, field


@dataclass
class Operation:
    work_order_id: str = "UNKNOWN"
    operation_id: str = "UNKNOWN"
    sequence: str | None = None
    work_center: str = "UNKNOWN"
    status: str = "Unknown"
    planned_start: str | None = None
    planned_end: str | None = None
    actual_start: str | None = None
    actual_end: str | None = None
    extended: dict = field(default_factory=dict)

    @classmethod
    def from_raw(cls, row: dict) -> "Operation":
        return cls(
            work_order_id=row.get("work_order_id") or row.get("build_id") or "UNKNOWN",
            operation_id=row.get("operation_id") or row.get("operation") or "UNKNOWN",
            sequence=row.get("sequence") or row.get("operation_seq"),
            work_center=row.get("work_center") or row.get("station_id") or "UNKNOWN",
            status=row.get("status") or "Unknown",
            planned_start=row.get("planned_start"),
            planned_end=row.get("planned_end"),
            actual_start=row.get("actual_start"),
            actual_end=row.get("actual_end"),
            extended=row.get("extended") or {},
        )

