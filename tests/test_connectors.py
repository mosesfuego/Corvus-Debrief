"""Tests for data connectors (SQLite, CSV, MES)."""
import os
import pytest
import sqlite3


class TestSQLiteConnector:
    """Tests for SQLite database connector."""

    @pytest.fixture
    def db_path(self):
        """Return path to test database."""
        return os.path.join(os.path.dirname(__file__), "test_factory.db")

    def test_database_exists(self, db_path):
        """Test that test database file exists."""
        assert os.path.exists(db_path), f"Database not found: {db_path}"

    def test_can_connect(self, db_path):
        """Test successful connection to database."""
        conn = sqlite3.connect(db_path)
        assert conn is not None
        conn.close()

    def test_builds_table_exists(self, db_path):
        """Test that builds table exists."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='builds'")
        result = cursor.fetchone()
        assert result is not None, "builds table not found"
        conn.close()

    def test_builds_has_expected_columns(self, db_path):
        """Test that builds table has expected columns."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(builds)")
        columns = {row[1] for row in cursor.fetchall()}
        expected = {'build_id', 'station_id', 'operator_id', 'start_time',
                    'planned_end', 'needed_by_date', 'target_quantity',
                    'completed_quantity', 'labor_hours', 'fulfillment_pct', 'status', 'notes'}
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"
        conn.close()

    def test_has_sample_data(self, db_path):
        """Test that database contains sample work orders."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM builds")
        count = cursor.fetchone()[0]
        assert count >= 2, f"Expected at least 2 builds, found {count}"
        conn.close()


class TestDataTypes:
    """Tests for data type handling."""

    @pytest.fixture
    def db_path(self):
        return os.path.join(os.path.dirname(__file__), "test_factory.db")

    def test_fulfillment_pct_is_numeric(self, db_path):
        """Test that fulfillment_pct is numeric."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT fulfillment_pct FROM builds LIMIT 1")
        result = cursor.fetchone()
        if result and result[0] is not None:
            assert isinstance(result[0], (int, float)), "fulfillment_pct should be numeric"
        conn.close()

    def test_status_values_valid(self, db_path):
        """Test that status values are from expected set."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        valid_statuses = {'Pending', 'In Progress', 'Completed', 'Blocked', 'Paused'}
        cursor.execute("SELECT DISTINCT status FROM builds WHERE status IS NOT NULL")
        statuses = {row[0] for row in cursor.fetchall()}
        assert statuses.issubset(valid_statuses), f"Unexpected statuses: {statuses - valid_statuses}"
        conn.close()
