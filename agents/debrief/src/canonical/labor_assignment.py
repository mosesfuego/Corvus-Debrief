"""Canonical labor/staffing assignment record."""

from dataclasses import dataclass, field


@dataclass
class LaborAssignment:
    operator_id: str = "UNKNOWN"
    work_order_id: str = "UNKNOWN"
    station_id: str = "UNKNOWN"
    shift: str | None = None
    certification: str | None = None
    availability: str = "Unknown"
    extended: dict = field(default_factory=dict)

    @classmethod
    def from_raw(cls, row: dict) -> "LaborAssignment":
        return cls(
            operator_id=row.get("operator_id") or row.get("employee_id") or "UNKNOWN",
            work_order_id=row.get("work_order_id") or row.get("build_id") or "UNKNOWN",
            station_id=row.get("station_id") or row.get("work_center") or "UNKNOWN",
            shift=row.get("shift"),
            certification=row.get("certification") or row.get("skill"),
            availability=row.get("availability") or row.get("status") or "Unknown",
            extended=row.get("extended") or {},
        )
