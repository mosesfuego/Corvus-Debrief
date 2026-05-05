"""
CSV MES Connector.
Accepts any CSV file and maps columns to Corvus schema
using the column_map defined in onboarding.yaml.

Unknown columns are preserved under build["extended"].
Missing schema fields use safe defaults — no errors.

To use:
    1. Run: python agents/debrief/src/tools/map_csv.py shared/data/your_file.csv
    2. Run: python agents/debrief/src/main.py --csv shared/data/your_file.csv
"""

import csv
import os
from collections import defaultdict
from connectors.base import BaseMESConnector
from intake.mapping_registry import normalize_status


OPTIONAL_FIELDS = [
    "build_id", "station_id", "operator_id", "start_time",
    "planned_end", "needed_by_date", "target_quantity",
    "completed_quantity", "labor_hours", "status", "notes"
]

FIELD_DEFAULTS = {
    "build_id":           "UNKNOWN",
    "station_id":         "UNKNOWN",
    "operator_id":        "UNKNOWN",
    "start_time":         None,
    "planned_end":        None,
    "needed_by_date":     None,
    "target_quantity":    0,
    "completed_quantity": 0,
    "labor_hours":        0.0,
    "status":             "Unknown",
    "notes":              "",
}


class CSVMESConnector(BaseMESConnector):
    """
    Connects to any CSV file using a column map
    defined in onboarding.yaml.
    File path must be passed via --csv flag.
    """
    
    def __init__(self, config: dict, onboarding: dict = None, file_path: str = None):
        self.config = config
        self.onboarding = onboarding or {}

        csv_config = self.onboarding.get("csv_connector", {})
        self.column_map = csv_config.get("column_map", {})
        self.status_map = csv_config.get("status_map", {})

        if not file_path:
            raise ValueError(
                "\n[CORVUS] No CSV file specified.\n"
                "Run with: python agents/debrief/src/main.py --csv shared/data/your_file.csv"
            )

        self.file_path = file_path
        self._cache = None

    def _validate_file(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(
                f"\n[CORVUS] CSV file not found: {self.file_path}\n"
                f"Check the path and try again."
            )
    def _build_maps(self, headers: list[str]) -> tuple[dict, list[str]]:
        """
        Build map: corvus_field → csv_column.
        Unknown columns preserved as extended.
        Case-insensitive matching.
        """
       
        # normalize headers for matching
        headers_lower = {h.lower(): h for h in headers}

        mapped = {}
        for field in OPTIONAL_FIELDS:
            csv_col = self.column_map.get(field)
            if not csv_col:
                continue

            # exact match first
            if csv_col in headers:
                mapped[field] = csv_col
            # case-insensitive fallback
            elif csv_col.lower() in headers_lower:
                actual_col = headers_lower[csv_col.lower()]
                mapped[field] = actual_col
                print(
                    f"[CORVUS] Case-insensitive column match: "
                    f"'{csv_col}' → '{actual_col}'"
                )

        mapped_csv_cols = set(mapped.values())
        extended_cols = [h for h in headers if h not in mapped_csv_cols]
        missing = [f for f in OPTIONAL_FIELDS if f not in mapped]

        print(
            f"[CORVUS] CSV ingest: {len(headers)} columns, "
            f"{len(mapped)} schema fields mapped, "
            f"{len(extended_cols)} extended"
            + (f", defaults for {missing}" if missing else "")
        )

        return mapped, extended_cols

    def _parse_row(
        self,
        row: dict,
        mapped: dict,
        extended_cols: list[str]
    ) -> dict:
        """
        Convert a raw CSV row to Corvus build schema.
        Known fields → typed and mapped.
        Unknown fields → preserved under "extended".
        Missing fields → safe defaults.
        """
        build = {}

        # extract known schema fields
        for field in OPTIONAL_FIELDS:
            csv_col = mapped.get(field)

            if csv_col and csv_col in row:
                raw_value = row[csv_col].strip() if row[csv_col] else ""

                if field in ["target_quantity", "completed_quantity"]:
                    try:
                        build[field] = int(float(raw_value)) if raw_value else 0
                    except ValueError:
                        build[field] = 0

                elif field == "labor_hours":
                    try:
                        build[field] = float(raw_value) if raw_value else 0.0
                    except ValueError:
                        build[field] = 0.0

                elif field == "status":
                    build[field] = self.status_map.get(
                        raw_value,
                        normalize_status(raw_value),
                    )

                else:
                    build[field] = raw_value if raw_value else None

            else:
                build[field] = FIELD_DEFAULTS.get(field)

        # preserve extended fields as-is
        build["extended"] = {
            col: row.get(col, "").strip()
            for col in extended_cols
        }

        return build

    def fetch_builds(self) -> list[dict]:
        """Read CSV and return list of builds in Corvus schema."""
        if self._cache is not None:
            return self._cache
        self._validate_file()

        builds = []
        with open(self.file_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = list(reader.fieldnames or [])
            mapped, extended_cols = self._build_maps(headers)

            for row in reader:
                build = self._parse_row(row, mapped, extended_cols)
                builds.append(build)

        self._cache = builds # cache after first read 
        print(f"[CORVUS] Loaded {len(builds)} builds from {self.file_path}")
        return self._cache

    def get_bottleneck_report(self) -> list[dict]:
        return [
            b for b in self.fetch_builds()
            if b.get("status") == "Blocked"
        ]

    def get_at_risk_report(self) -> list[dict]:
        at_risk = []
        for build in self.fetch_builds():
            status = build.get("status")
            if status != "Completed" and self._is_late(build):
                at_risk.append(build)
        return at_risk

    def get_efficiency_by_station(self) -> dict:
        stats = defaultdict(lambda: {
            "total_target": 0,
            "total_completed": 0,
            "labor_hours": 0.0,
            "order_count": 0
        })

        for build in self.fetch_builds():
            s = build.get("station_id", "UNKNOWN")
            stats[s]["total_target"]    += build.get("target_quantity", 0)
            stats[s]["total_completed"] += build.get("completed_quantity", 0)
            stats[s]["labor_hours"]     += build.get("labor_hours", 0.0)
            stats[s]["order_count"]     += 1

        return {
            station: {
                "fulfillment_pct": round(
                    v["total_completed"] / v["total_target"] * 100, 1
                ) if v["total_target"] > 0 else 0,
                "labor_hours": v["labor_hours"],
                "order_count": v["order_count"]
            }
            for station, v in stats.items()
        }
