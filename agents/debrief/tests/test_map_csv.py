"""Tests for CSV mapping behavior."""

import csv
import os
import sys

import pytest

_THIS_FILE = os.path.abspath(__file__)
_TESTS_DIR = os.path.dirname(_THIS_FILE)
_AGENT_ROOT = os.path.dirname(_TESTS_DIR)
_SRC_DIR = os.path.join(_AGENT_ROOT, "src")
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_AGENT_ROOT))
_SHARED_DIR = os.path.join(_PROJECT_ROOT, "shared")

sys.path.insert(0, _PROJECT_ROOT)
sys.path.insert(0, _SHARED_DIR)
sys.path.insert(0, _SRC_DIR)

from tools import map_csv


def write_csv(path, headers, rows):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def test_fingerprint_ignores_data_changes(tmp_path):
    csv_path = tmp_path / "builds.csv"
    headers = ["Job_ID", "Status"]

    write_csv(csv_path, headers, [{"Job_ID": "WO-1", "Status": "Running"}])
    first = map_csv.get_csv_fingerprint(str(csv_path))

    write_csv(csv_path, headers, [{"Job_ID": "WO-2", "Status": "Blocked"}])
    second = map_csv.get_csv_fingerprint(str(csv_path))

    assert first == second


def test_heuristics_resolve_common_columns():
    proposal = map_csv.propose_mapping_with_heuristics([
        "Job_ID",
        "Work_Center",
        "Operator_ID",
        "Status",
        "Comments",
    ])

    mapping = proposal["mapping"]
    assert mapping["build_id"]["csv_column"] == "Job_ID"
    assert mapping["station_id"]["csv_column"] == "Work_Center"
    assert mapping["operator_id"]["csv_column"] == "Operator_ID"
    assert mapping["status"]["csv_column"] == "Status"
    assert mapping["notes"]["csv_column"] == "Comments"


def test_mapping_falls_back_when_llm_unavailable(monkeypatch):
    def fail_llm(*_args, **_kwargs):
        raise RuntimeError("model retired")

    monkeypatch.setattr(map_csv, "propose_mapping_with_llm", fail_llm)

    proposal = map_csv.build_mapping_proposal(
        ["Job_ID", "Work_Center", "Status", "Timestamp", "Comments"],
        [
            {
                "Job_ID": "WO-1",
                "Work_Center": "SMT",
                "Status": "Running",
                "Timestamp": "2026-01-01T08:00:00",
                "Comments": "ok",
            }
        ],
        {"agents": {"api_key": "fake"}},
    )

    assert proposal["mapping"]["build_id"]["csv_column"] == "Job_ID"
    assert proposal["mapping"]["status"]["csv_column"] == "Status"
    assert proposal["status_map"]["Running"] == "In Progress"


def test_validate_mapping_rejects_missing_required_field():
    clean_map, _, issues = map_csv.validate_mapping(
        {"status": "Status"},
        {},
        ["Job_ID", "Status"],
    )

    assert clean_map == {"status": "Status"}
    assert "Required field is not mapped: build_id" in issues


def test_validate_mapping_ignores_missing_llm_column():
    clean_map, _, issues = map_csv.validate_mapping(
        {"build_id": "NotAColumn", "status": "Status"},
        {},
        ["Job_ID", "Status"],
        require_required=False,
    )

    assert clean_map == {"status": "Status"}
    assert "'build_id' maps to missing CSV column 'NotAColumn'" in issues


def test_display_and_confirm_blocks_required_missing_in_yes_mode():
    proposal = {
        "mapping": {
            "status": {"csv_column": "Status", "confidence": 0.95},
        },
        "status_map": {},
    }

    with pytest.raises(ValueError, match="required fields"):
        map_csv.display_and_confirm_mapping(
            proposal,
            ["Job_ID", "Status"],
            yes=True,
        )


def test_run_dry_run_does_not_write_onboarding(tmp_path):
    csv_path = tmp_path / "builds.csv"
    onboarding_path = tmp_path / "onboarding.yaml"
    write_csv(
        csv_path,
        [
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
        ],
        [
            {
                "build_id": "WO-1",
                "station_id": "Line 1",
                "operator_id": "OP-1",
                "start_time": "2026-01-01T08:00:00",
                "planned_end": "2026-01-01T09:00:00",
                "needed_by_date": "2026-01-01T10:00:00",
                "target_quantity": "10",
                "completed_quantity": "5",
                "labor_hours": "1",
                "status": "In Progress",
                "notes": "ok",
            }
        ],
    )
    original = "schema_version: '1.0'\ncompany: TestCo\nsite: Test Site\n"
    onboarding_path.write_text(original)

    map_csv.run(
        str(csv_path),
        str(onboarding_path),
        force=True,
        yes=True,
        dry_run=True,
    )

    assert onboarding_path.read_text() == original
