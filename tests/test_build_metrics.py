"""
Unit tests for BuildMetrics analytics layer.

Tests deterministic business logic with fixed timestamps.
No dynamic utcnow() - all tests use explicit datetime values.
"""

from datetime import datetime, timezone, timedelta
import pytest

from src.analytics.build_metrics import BuildMetrics, ThresholdConfig


class TestBuildMetrics:
    """Test suite for BuildMetrics analytics engine."""

    def setup_method(self):
        """Set up test fixtures with known thresholds."""
        # 60 min delay threshold, 30 min stall threshold
        self.config = ThresholdConfig(
            delay_threshold_minutes=60.0,
            stall_threshold_minutes=30.0
        )
        self.analytics = BuildMetrics(self.config)

        # Fixed reference time for all tests
        self.now = datetime(2024, 3, 15, 12, 0, 0, tzinfo=timezone.utc)

    #
    # COMPLETED BUILDS
    #

    def test_completed_build_under_threshold(self):
        """
        COMPLETED build under delay threshold should NOT be flagged.
        Rule A: delayed = total_active > threshold (45min < 60min)
        """
        # Build completed in 45 minutes (under 60min threshold)
        build = {
            'workorder_id': 'WO-001',
            'status': 'COMPLETED',
            'started_at': datetime(2024, 3, 15, 11, 0, 0, tzinfo=timezone.utc),
            'last_status_change': datetime(2024, 3, 15, 11, 45, 0, tzinfo=timezone.utc),
            'completed_at': datetime(2024, 3, 15, 11, 45, 0, tzinfo=timezone.utc)
        }

        result = self.analytics.evaluate([build], self.now)
        enriched = result['builds'][0]
        metrics = enriched['metrics']

        assert metrics['total_active_minutes'] == 45.0
        assert metrics['delayed'] is False
        assert metrics['stalled'] is False

    def test_completed_build_over_threshold(self):
        """
        COMPLETED build over delay threshold SHOULD be flagged delayed.
        Rule A: delayed = total_active > threshold (90min > 60min)
        """
        # Build completed in 90 minutes (over 60min threshold)
        build = {
            'workorder_id': 'WO-002',
            'status': 'COMPLETED',
            'started_at': datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc),
            'last_status_change': datetime(2024, 3, 15, 11, 30, 0, tzinfo=timezone.utc),
            'completed_at': datetime(2024, 3, 15, 11, 30, 0, tzinfo=timezone.utc)
        }

        result = self.analytics.evaluate([build], self.now)
        enriched = result['builds'][0]
        metrics = enriched['metrics']

        assert metrics['total_active_minutes'] == 90.0
        assert metrics['delayed'] is True
        assert metrics['stalled'] is False

    #
    # IN_PROGRESS BUILDS
    #

    def test_in_progress_build_delayed(self):
        """
        IN_PROGRESS build exceeding delay threshold SHOULD be flagged.
        Rule B: delayed = (now - started_at) > threshold (120min > 60min)
        """
        # Build started 2 hours ago (over 60min threshold)
        build = {
            'workorder_id': 'WO-003',
            'status': 'IN_PROGRESS',
            'started_at': datetime(2024, 3, 15, 10, 0, 0, tzinfo=timezone.utc),
            'last_status_change': datetime(2024, 3, 15, 11, 30, 0, tzinfo=timezone.utc),
            'completed_at': None
        }

        result = self.analytics.evaluate([build], self.now)
        enriched = result['builds'][0]
        metrics = enriched['metrics']

        assert metrics['total_active_minutes'] == 120.0
        assert metrics['minutes_in_current_state'] == 30.0  # 11:30 to 12:00
        assert metrics['delayed'] is True
        assert metrics['stalled'] is False  # 30min == threshold (not >)

    def test_in_progress_build_stalled(self):
        """
        IN_PROGRESS build with long status gap SHOULD be flagged stalled.
        Rule B: stalled = (now - last_status_change) > threshold
        """
        # Build last changed status 45 minutes ago (over 30min threshold)
        build = {
            'workorder_id': 'WO-004',
            'status': 'IN_PROGRESS',
            'started_at': datetime(2024, 3, 15, 11, 0, 0, tzinfo=timezone.utc),
            'last_status_change': datetime(2024, 3, 15, 11, 15, 0, tzinfo=timezone.utc),
            'completed_at': None
        }

        result = self.analytics.evaluate([build], self.now)
        enriched = result['builds'][0]
        metrics = enriched['metrics']

        assert metrics['total_active_minutes'] == 60.0
        assert metrics['minutes_in_current_state'] == 45.0  # 11:15 to 12:00
        assert metrics['stalled'] is True
        assert metrics['delayed'] is False  # exactly 60min, not > 60min

    #
    # PAUSED BUILDS
    #

    def test_paused_build_stalled(self):
        """
        PAUSED build exceeding stall threshold SHOULD be flagged stalled.
        Rule C: stalled = total_paused > threshold (60min > 30min)
        """
        # Build paused 1 hour ago
        build = {
            'workorder_id': 'WO-005',
            'status': 'PAUSED',
            'started_at': datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc),
            'last_status_change': datetime(2024, 3, 15, 11, 0, 0, tzinfo=timezone.utc),
            'completed_at': None
        }

        result = self.analytics.evaluate([build], self.now)
        enriched = result['builds'][0]
        metrics = enriched['metrics']

        assert metrics['total_paused_minutes'] == 60.0
        assert metrics['minutes_in_current_state'] == 60.0
        assert metrics['stalled'] is True
        assert metrics['delayed'] is False
        assert metrics['total_active_minutes'] is None  # No active time for PAUSED

    def test_paused_build_not_stalled(self):
        """
        PAUSED build under stall threshold should NOT be flagged.
        Rule C: stalled = total_paused > threshold (15min < 30min)
        """
        # Build paused 15 minutes ago
        build = {
            'workorder_id': 'WO-006',
            'status': 'PAUSED',
            'started_at': datetime(2024, 3, 15, 11, 0, 0, tzinfo=timezone.utc),
            'last_status_change': datetime(2024, 3, 15, 11, 45, 0, tzinfo=timezone.utc),
            'completed_at': None
        }

        result = self.analytics.evaluate([build], self.now)
        enriched = result['builds'][0]
        metrics = enriched['metrics']

        assert metrics['total_paused_minutes'] == 15.0
        assert metrics['stalled'] is False

    #
    # NOT_STARTED BUILDS
    #

    def test_not_started_build(self):
        """
        NOT_STARTED build has no time accumulation and no flags.
        Rule D: delayed = False, stalled = False
        """
        build = {
            'workorder_id': 'WO-007',
            'status': 'NOT_STARTED',
            'started_at': None,
            'last_status_change': None,
            'completed_at': None
        }

        result = self.analytics.evaluate([build], self.now)
        enriched = result['builds'][0]
        metrics = enriched['metrics']

        assert metrics['total_active_minutes'] is None
        assert metrics['total_paused_minutes'] is None
        assert metrics['minutes_in_current_state'] is None
        assert metrics['delayed'] is False
        assert metrics['stalled'] is False

    #
    # EMPTY INPUT
    #

    def test_empty_list_input(self):
        """
        Empty build list should return empty builds and zero summary.
        """
        result = self.analytics.evaluate([], self.now)

        assert result['builds'] == []
        assert result['summary']['total_builds'] == 0
        assert result['summary']['delayed'] == 0
        assert result['summary']['stalled'] == 0

    #
    # SUMMARY VERIFICATION
    #
