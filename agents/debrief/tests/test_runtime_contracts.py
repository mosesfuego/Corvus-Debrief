"""Regression tests for CLI/runtime contracts."""

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "agents" / "debrief" / "src"
SHARED_DIR = PROJECT_ROOT / "shared"

for path in (str(SRC_DIR), str(SHARED_DIR), str(PROJECT_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from connectors.api_connector import APIMESConnector
from connectors.csv_connector import CSVMESConnector
from utils.config import load_config


def test_load_config_allows_missing_env_placeholder(tmp_path, monkeypatch):
    monkeypatch.delenv("CORVUS_TEST_MISSING_KEY", raising=False)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
mes_type: csv
agents:
  api_key: ${CORVUS_TEST_MISSING_KEY}
""".lstrip()
    )

    config = load_config(str(config_path))

    assert config["agents"]["api_key"] is None


def test_api_connector_returns_full_mes_schema():
    builds = APIMESConnector({}).fetch_builds()

    required_fields = {
        "build_id",
        "station_id",
        "operator_id",
        "start_time",
        "planned_end",
        "needed_by_date",
        "target_quantity",
        "completed_quantity",
        "labor_hours",
        "status",
        "notes",
    }
    assert builds
    assert required_fields.issubset(builds[0])


def test_csv_at_risk_uses_datetime_comparison(tmp_path):
    csv_path = tmp_path / "builds.csv"
    headers = ["Job", "Status", "Planned", "Needed"]
    rows = [
        {
            "Job": "WO-TZ-001",
            "Status": "In Progress",
            "Planned": "2026-01-01T00:00:00+02:00",
            "Needed": "2025-12-31T23:30:00+00:00",
        }
    ]
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    onboarding = {
        "csv_connector": {
            "column_map": {
                "build_id": "Job",
                "status": "Status",
                "planned_end": "Planned",
                "needed_by_date": "Needed",
            }
        }
    }
    connector = CSVMESConnector(
        {"mes_type": "csv"},
        onboarding,
        file_path=str(csv_path),
    )

    assert connector.get_at_risk_report() == []
