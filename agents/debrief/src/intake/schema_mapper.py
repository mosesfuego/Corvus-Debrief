"""Schema mapping helpers shared by CSV and future API/database intake."""

from intake.mapping_registry import (
    WORK_ORDER_SCHEMA,
    VALID_STATUSES,
    aliases_for,
    normalize_name,
    resolve_header,
)


def propose_mapping_with_heuristics(
    headers: list[str],
    source_type: str = "work_order",
) -> dict:
    """Map obvious fields before spending LLM tokens."""
    normalized_headers = {normalize_name(h): h for h in headers}
    mapping = {}

    for field, aliases in aliases_for(source_type).items():
        match = None
        for alias in aliases:
            match = normalized_headers.get(normalize_name(alias))
            if match:
                break

        if not match:
            compact_field = normalize_name(field).replace("_", "")
            for normalized, header in normalized_headers.items():
                if normalized.replace("_", "") == compact_field:
                    match = header
                    break

        mapping[field] = {
            "csv_column": match,
            "confidence": 0.95 if match else 0.0,
            "source": "heuristic" if match else "unmapped",
        }

    return {"mapping": mapping, "status_map": {}, "unmapped_columns": []}


def validate_mapping(
    column_map: dict,
    status_map: dict,
    headers: list[str],
    required_fields: list[str],
    schema: dict | None = None,
) -> tuple[dict, dict, list[str]]:
    """Normalize mapped headers and report invalid/missing fields."""
    schema = schema or WORK_ORDER_SCHEMA
    clean_map = {}
    issues = []

    for field, csv_col in column_map.items():
        if field not in schema:
            issues.append(f"Unknown Corvus field ignored: {field}")
            continue
        actual_header = resolve_header(csv_col, headers)
        if csv_col and not actual_header:
            issues.append(f"'{field}' maps to missing CSV column '{csv_col}'")
            continue
        if actual_header:
            clean_map[field] = actual_header

    for field in required_fields:
        if field not in clean_map:
            issues.append(f"Required field is not mapped: {field}")

    clean_status_map = {}
    for raw_status, normalized_status in (status_map or {}).items():
        if normalized_status in VALID_STATUSES:
            clean_status_map[raw_status] = normalized_status
        else:
            issues.append(
                f"Status '{raw_status}' maps to unsupported value "
                f"'{normalized_status}'"
            )

    return clean_map, clean_status_map, issues

