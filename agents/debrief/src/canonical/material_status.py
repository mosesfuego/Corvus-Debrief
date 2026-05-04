"""Canonical material or kitting status record."""

from dataclasses import dataclass, field


@dataclass
class MaterialStatus:
    part_number: str = "UNKNOWN"
    work_order_id: str = "UNKNOWN"
    status: str = "Unknown"
    shortage_quantity: float = 0.0
    expected_receipt: str | None = None
    supplier: str | None = None
    notes: str = ""
    extended: dict = field(default_factory=dict)

    @classmethod
    def from_raw(cls, row: dict) -> "MaterialStatus":
        return cls(
            part_number=row.get("part_number") or row.get("component_part") or "UNKNOWN",
            work_order_id=row.get("work_order_id") or row.get("build_id") or "UNKNOWN",
            status=row.get("status") or row.get("kit_status") or "Unknown",
            shortage_quantity=_float(row.get("shortage_quantity") or row.get("shortage_qty")),
            expected_receipt=row.get("expected_receipt"),
            supplier=row.get("supplier"),
            notes=row.get("notes") or row.get("comments") or "",
            extended=row.get("extended") or {},
        )


def _float(value) -> float:
    try:
        return float(value) if value not in (None, "") else 0.0
    except (TypeError, ValueError):
        return 0.0

