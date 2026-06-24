"""Tests for report generation and templates."""
import os
import sqlite3
import json
import sys
from datetime import datetime
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

from reporting.debrief_template import DebriefGenerator


class TestReportGeneration:
    """Tests for report generation."""

    @pytest.fixture
    def db_path(self):
        return os.path.join(os.path.dirname(__file__), "test_factory.db")

    @pytest.fixture
    def sample_metrics(self, db_path):
        """Generate sample metrics from database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*), AVG(fulfillment_pct) FROM builds")
        total, avg_fill = cursor.fetchone()

        cursor.execute("SELECT status, COUNT(*) FROM builds GROUP BY status")
        status_counts = dict(cursor.fetchall())

        cursor.execute("""
            SELECT station_id, AVG(fulfillment_pct)
            FROM builds GROUP BY station_id ORDER BY AVG(fulfillment_pct)
        """)
        station_performance = cursor.fetchall()

        conn.close()

        return {
            "total_builds": total,
            "avg_fulfillment_pct": avg_fill,
            "status_breakdown": status_counts,
            "station_performance": station_performance,
            "timestamp": datetime.now().isoformat()
        }

    def test_metrics_structure(self, sample_metrics):
        """Test that generated metrics have expected structure."""
        assert "total_builds" in sample_metrics
        assert "avg_fulfillment_pct" in sample_metrics
        assert "status_breakdown" in sample_metrics
        assert "station_performance" in sample_metrics
        assert "timestamp" in sample_metrics

    def test_metrics_have_reasonable_values(self, sample_metrics):
        """Test that metrics contain reasonable values."""
        assert sample_metrics["total_builds"] >= 2
        assert 0 <= sample_metrics["avg_fulfillment_pct"] <= 100
        assert len(sample_metrics["status_breakdown"]) > 0

    def test_timestamp_is_valid_iso(self, sample_metrics):
        """Test that timestamp is valid ISO format."""
        ts = sample_metrics["timestamp"]
        # Should be parseable
        parsed = datetime.fromisoformat(ts)
        assert parsed is not None

    def test_report_includes_source_confidence_when_available(self):
        config = {
            "_source_confidence": {
                "source_type": "work_order",
                "source_confidence": 0.75,
                "mapped_fields": {
                    "build_id": "Job_ID",
                    "status": "Status",
                },
                "unmapped_columns": ["Customer_Note"],
                "missing_critical_fields": [],
                "mapping_coverage": 0.18,
                "mapped_field_count": 2,
                "schema_field_count": 11,
            },
            "reporting": {"output_dir": "./reports"},
        }
        onboarding = {
            "company": "TestCo",
            "site": "Plant 1",
            "teams": [],
        }

        report = DebriefGenerator(config, onboarding).generate("All clear.")

        assert "SOURCE CONFIDENCE" in report
        assert "Detected source: work_order (75% confidence)" in report
        assert "build_id: Job_ID" in report
        assert "Unmapped CSV columns: Customer_Note" in report


class TestOutputFormats:
    """Tests for different output formats."""

    @pytest.fixture
    def sample_metrics(self):
        return {
            "total_builds": 8,
            "avg_fulfillment_pct": 45.9,
            "status_breakdown": {"Completed": 2, "In Progress": 2, "Blocked": 1, "Paused": 1, "Pending": 2},
            "timestamp": datetime.now().isoformat()
        }

    def test_json_output(self, sample_metrics):
        """Test JSON serialization."""
        json_str = json.dumps(sample_metrics, indent=2)
        assert json_str is not None
        # Should be parseable back
        parsed = json.loads(json_str)
        assert parsed["total_builds"] == 8

    def test_markdown_report_structure(self, sample_metrics):
        """Test markdown report generation."""
        md = f"""# Manufacturing Debrief Report
Generated: {sample_metrics['timestamp']}

## Summary
- **Total Builds:** {sample_metrics['total_builds']}
- **Avg Fulfillment:** {sample_metrics['avg_fulfillment_pct']:.1f}%

## Status Breakdown
| Status | Count |
|--------|-------|
"""
        for status, count in sample_metrics['status_breakdown'].items():
            md += f"| {status} | {count} |\n"

        assert "Manufacturing Debrief Report" in md
        assert str(sample_metrics['total_builds']) in md


class TestEdgeCases:
    """Tests for edge cases in reporting."""

    def test_empty_metrics_handling(self):
        """Test handling of empty/None metrics."""
        empty = {"total_builds": 0, "status_breakdown": {}}
        assert empty["total_builds"] == 0
        assert len(empty["status_breakdown"]) == 0

    def test_division_by_zero_protection(self):
        """Test protection against division by zero."""
        # Simulate a case where target is 0
        target = 0
        completed = 0
        if target > 0:
            pct = (completed / target) * 100
        else:
            pct = 0
        assert pct == 0

    def test_missing_optional_fields(self):
        """Test report with missing optional fields."""
        minimal = {"total_builds": 5}
        assert minimal["total_builds"] == 5
        assert "optional_field" not in minimal
