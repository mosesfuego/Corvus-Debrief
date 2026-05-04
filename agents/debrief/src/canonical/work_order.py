"""Canonical work order record."""

from dataclasses import dataclass, field


@dataclass
class WorkOrder:
    build_id: str = "UNKNOWN"
    station_id: str = "UNKNOWN"
    operator_id: str = "UNKNOWN"
    start_time: str | None = None
    planned_end: str | None = None
    needed_by_date: str | None = None
    target_quantity: int = 0
    completed_quantity: int = 0
    labor_hours: float = 0.0
    status: str = "Unknown"
    notes: str = ""
    extended: dict = field(default_factory=dict)

    @classmethod
    def from_raw(cls, row: dict) -> "WorkOrder":
        return cls(
            build_id=row.get("build_id") or "UNKNOWN",
            station_id=row.get("station_id") or "UNKNOWN",
            operator_id=row.get("operator_id") or "UNKNOWN",
            start_time=row.get("start_time"),
            planned_end=row.get("planned_end"),
            needed_by_date=row.get("needed_by_date"),
            target_quantity=_int(row.get("target_quantity")),
            completed_quantity=_int(row.get("completed_quantity")),
            labor_hours=_float(row.get("labor_hours")),
            status=row.get("status") or "Unknown",
            notes=row.get("notes") or "",
            extended=row.get("extended") or {},
        )

    def to_dict(self) -> dict:
        return {
            "build_id": self.build_id,
            "station_id": self.station_id,
            "operator_id": self.operator_id,
            "start_time": self.start_time,
            "planned_end": self.planned_end,
            "needed_by_date": self.needed_by_date,
            "target_quantity": self.target_quantity,
            "completed_quantity": self.completed_quantity,
            "labor_hours": self.labor_hours,
            "status": self.status,
            "notes": self.notes,
            "extended": self.extended,
        }


def _int(value) -> int:
    try:
        return int(float(value)) if value not in (None, "") else 0
    except (TypeError, ValueError):
        return 0


def _float(value) -> float:
    try:
        return float(value) if value not in (None, "") else 0.0
    except (TypeError, ValueError):
        return 0.0

