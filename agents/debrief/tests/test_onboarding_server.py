import os
import sys

_THIS_FILE = os.path.abspath(__file__)
_TESTS_DIR = os.path.dirname(_THIS_FILE)
_AGENT_ROOT = os.path.dirname(_TESTS_DIR)
_SRC_DIR = os.path.join(_AGENT_ROOT, "src")
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_AGENT_ROOT))
_SHARED_DIR = os.path.join(_PROJECT_ROOT, "shared")

sys.path.insert(0, _SRC_DIR)
sys.path.insert(0, _SHARED_DIR)
sys.path.insert(0, _PROJECT_ROOT)

from onboarding import merge_onboarding


def test_merge_onboarding_updates_wizard_fields_and_preserves_connector():
    existing = {
        "schema_version": "1.0",
        "company": "OldCo",
        "site": "Plant 1",
        "csv_connector": {
            "column_map": {"build_id": "Job_ID"},
        },
    }
    incoming = {
        "company": "AeroCore",
        "site": "Plant A",
        "thresholds": {"delay_minutes": 30, "stall_minutes": 20},
        "teams": [
            {
                "name": "Production",
                "cares_about": ["blocked builds"],
                "watch_signals": ["stalled_build"],
                "meeting": "7:30am",
            }
        ],
    }

    merged = merge_onboarding(existing, incoming)

    assert merged["company"] == "AeroCore"
    assert merged["site"] == "Plant A"
    assert merged["thresholds"]["delay_minutes"] == 30
    assert merged["teams"][0]["watch_signals"] == ["stalled_build"]
    assert merged["csv_connector"]["column_map"] == {"build_id": "Job_ID"}


def test_merge_onboarding_ignores_non_wizard_fields_from_request():
    merged = merge_onboarding(
        {"schema_version": "1.0"},
        {"company": "AeroCore", "csv_connector": {"column_map": {}}},
    )

    assert merged["company"] == "AeroCore"
    assert "csv_connector" not in merged
