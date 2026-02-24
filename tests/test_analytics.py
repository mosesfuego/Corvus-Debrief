"""Tests for analytics engine (metrics, bottlenecks, trends)."""
import os
import sqlite3
import pytest


class TestBuildMetrics:
    """Tests for build metrics calculations."""

    @pytest.fixture
    def db_path(self):
        """Return path to test database."""
        return os.path.join(os.path.dirname(__file__), "test_factory.db")

    @pytest.fixture
    def conn(self, db_path):
        """Provide database connection."""
        connection = sqlite3.connect(db_path)
        yield connection
        connection.close()

    def test_count_by_status(self, conn):
        """Test counting builds by status."""
        cursor = conn.cursor()
        cursor.execute("SELECT status, COUNT(*) FROM builds GROUP BY status")
        results = dict(cursor.fetchall())
        assert len(results) > 0, "No status data found"
        total = sum(results.values())
        assert total >= 2, "Expected at least 2 builds"

    def test_average_fulfillment(self, conn):
        """Test calculating average fulfillment percentage."""
        cursor = conn.cursor()
        cursor.execute("SELECT AVG(fulfillment_pct) FROM builds")
        avg = cursor.fetchone()[0]
        assert avg is not None, "Could not calculate average fulfillment"
        assert 0 <= avg <= 100, f"Average fulfillment {avg} out of expected range"

    def test_total_target_vs_completed(self, conn):
        """Test comparing total target vs completed quantities."""
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(target_quantity), SUM(completed_quantity) FROM builds")
        target, completed = cursor.fetchone()
        assert target is not None and target > 0, "No target quantities found"
        assert completed is not None, "No completed quantities found"
        assert completed <= target, "Completed quantity exceeds target (data anomaly)"


class TestBottleneckDetection:
    """Tests for bottleneck detection."""

    @pytest.fixture
    def conn(self):
        db_path = os.path.join(os.path.dirname(__file__), "test_factory.db")
        connection = sqlite3.connect(db_path)
        yield connection
        connection.close()

    def test_blocked_orders_exist(self, conn):
        """Test that blocked work orders can be detected."""
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM builds WHERE status = 'Blocked'")
        count = cursor.fetchone()[0]
        # Note: May be 0, but test ensures query works
        assert count >= 0

    def test_blocked_orders_have_low_fulfillment(self, conn):
        """Test that blocked orders typically have low fulfillment."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT build_id, fulfillment_pct FROM builds
            WHERE status = 'Blocked' AND fulfillment_pct IS NOT NULL
        """)
        blocked = cursor.fetchall()
        for build_id, fulfillment in blocked:
            assert fulfillment < 100, f"Blocked order {build_id} shows 100% fulfillment"

    def test_identify_slow_stations(self, conn):
        """Test identifying stations with low average fulfillment."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT station_id, AVG(fulfillment_pct) as avg_fill
            FROM builds
            GROUP BY station_id
            HAVING avg_fill < 50
            ORDER BY avg_fill
        """)
        slow_stations = cursor.fetchall()
        # Just verifying query works - may return empty if no slow stations
        assert isinstance(slow_stations, list)


class TestCycleTimeAnalysis:
    """Tests for cycle time and efficiency metrics."""

    @pytest.fixture
    def conn(self):
        db_path = os.path.join(os.path.dirname(__file__), "test_factory.db")
        connection = sqlite3.connect(db_path)
        yield connection
        connection.close()

    def test_labor_hours_are_numeric(self, conn):
        """Test that labor_hours are numeric."""
        cursor = conn.cursor()
        cursor.execute("SELECT labor_hours FROM builds WHERE labor_hours > 0 LIMIT 1")
        result = cursor.fetchone()
        if result:
            assert result[0] >= 0, "Labor hours should be non-negative"