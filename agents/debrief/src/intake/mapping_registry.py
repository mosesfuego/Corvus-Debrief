"""Canonical field registry and deterministic mapping metadata."""

import re


WORK_ORDER_SCHEMA = {
    "build_id": "Unique identifier for the work order or job",
    "station_id": "Machine, line, or workstation where the job runs",
    "operator_id": "Technician or operator assigned to the job",
    "start_time": "When the job started (ISO datetime or similar)",
    "planned_end": "When the job is scheduled to finish",
    "needed_by_date": "Customer or production deadline for this job",
    "target_quantity": "How many units are planned for this job",
    "completed_quantity": "How many units have been completed so far",
    "labor_hours": "Hours of labor logged against this job",
    "status": "Current state of the job",
    "notes": "Any comments, flags, or free text about this job",
}

SOURCE_TYPES = {
    "work_order": {
        "label": "Work Orders / Jobs / Builds",
        "required_fields": ["build_id", "status"],
        "schema": WORK_ORDER_SCHEMA,
    },
    "operation": {
        "label": "Operations / Routing Steps",
        "required_fields": ["work_order_id", "operation_id"],
        "schema": {},
    },
    "quality_issue": {
        "label": "Quality / Inspection / NCR",
        "required_fields": [],
        "schema": {},
    },
    "material_status": {
        "label": "Materials / Inventory / Kitting",
        "required_fields": [],
        "schema": {},
    },
    "labor_assignment": {
        "label": "Labor / Staffing / Certifications",
        "required_fields": [],
        "schema": {},
    },
    "equipment": {
        "label": "Equipment / Downtime / Maintenance",
        "required_fields": [],
        "schema": {},
    },
    "unknown": {
        "label": "Unknown Manufacturing Export",
        "required_fields": [],
        "schema": {},
    },
}

COMMON_ALIASES = {
    "build_id": [
        "build_id", "build", "job", "job_id", "job_number", "work_order",
        "workorder", "work_order_id", "wo", "wo_id", "order", "order_id",
    ],
    "station_id": [
        "station_id", "station", "work_center", "workcenter", "work_cell",
        "cell", "machine", "machine_id", "line", "line_id", "operation",
    ],
    "operator_id": [
        "operator_id", "operator", "technician", "tech", "employee",
        "employee_id", "personnel", "assigned_operator",
    ],
    "start_time": [
        "start_time", "started_at", "start", "timestamp", "time",
        "created_at", "actual_start",
    ],
    "planned_end": [
        "planned_end", "scheduled_end", "planned_finish", "finish_time",
        "end_time", "expected_completion", "planned_complete",
    ],
    "needed_by_date": [
        "needed_by_date", "needed_by", "due_date", "deadline",
        "customer_due", "required_by", "ship_date", "promise_date",
    ],
    "target_quantity": [
        "target_quantity", "target_qty", "qty_required", "quantity",
        "order_qty", "planned_qty", "required_qty", "target",
    ],
    "completed_quantity": [
        "completed_quantity", "completed_qty", "qty_complete", "qty_done",
        "done_qty", "good_qty", "produced_qty", "completed",
    ],
    "labor_hours": [
        "labor_hours", "labour_hours", "hours", "work_hours", "logged_hours",
        "man_hours", "runtime_hours",
    ],
    "status": [
        "status", "state", "job_status", "order_status", "current_status",
        "work_order_status",
    ],
    "notes": [
        "notes", "comments", "comment", "description", "remarks",
        "message", "issue", "reason",
    ],
}

SOURCE_TYPE_KEYWORDS = {
    "work_order": [
        "work_order", "workorder", "job", "build", "order_id", "station",
        "work_center", "qty", "quantity", "status",
    ],
    "operation": [
        "operation", "op_seq", "routing", "step", "work_center",
        "setup", "queue",
    ],
    "quality_issue": [
        "inspection", "defect", "ncr", "mrb", "quality", "result",
        "failure", "rework", "scrap",
    ],
    "material_status": [
        "material", "part", "lot", "kit", "inventory", "shortage",
        "supplier", "receipt",
    ],
    "labor_assignment": [
        "operator", "employee", "shift", "certification", "skill",
        "clock", "labor",
    ],
    "equipment": [
        "machine", "asset", "downtime", "maintenance", "tool",
        "fixture", "calibration",
    ],
}

VALID_STATUSES = {"Pending", "In Progress", "Completed", "Blocked", "Paused"}
REQUIRED_WORK_ORDER_FIELDS = SOURCE_TYPES["work_order"]["required_fields"]


def normalize_name(value: str) -> str:
    """Normalize a header or field name for matching."""
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def resolve_header(csv_col: str | None, headers: list[str]) -> str | None:
    """Return the actual CSV header for a proposed column, or None."""
    if not csv_col:
        return None
    if csv_col in headers:
        return csv_col
    normalized_headers = {normalize_name(h): h for h in headers}
    return normalized_headers.get(normalize_name(csv_col))


def aliases_for(source_type: str) -> dict:
    """Return deterministic aliases for a source type."""
    if source_type == "work_order":
        return COMMON_ALIASES
    return {}

