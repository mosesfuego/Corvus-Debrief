"""
Build Metrics Analytics Layer

Pure deterministic logic for interpreting MES build state into actionable signals.
No database access. No logging. Testable functions only.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


@dataclass
class ThresholdConfig:
    """Configuration thresholds for analytics."""
    delay_threshold_minutes: float = 60.0
    stall_threshold_minutes: float = 30.0


@dataclass
class BuildMetricsResult:
    """Result container for a single build's computed metrics."""
    total_active_minutes: Optional[float] = None
    total_paused_minutes: Optional[float] = None
    minutes_in_current_state: Optional[float] = None
    delayed: bool = False
    stalled: bool = False


class BuildMetrics:
    """
    Analytics engine for manufacturing build metrics.
    Converts raw MES build state into operational insights:
    - Time accumulation calculations
    - Threshold-based flagging (delayed, stalled)
    - System-wide summary generation
    """

    def __init__(self, config: Optional[ThresholdConfig] = None):
        """Initialize with threshold configuration."""
        self.config = config or ThresholdConfig()

    def _calculate_minutes(self, start: datetime, end: datetime) -> float:
        """Calculate minutes between two datetime objects."""
        return (end - start).total_seconds() / 60.0

    def _process_completed(self, build: Dict[str, Any], now: datetime) -> BuildMetricsResult:
        """
        Process COMPLETED build.
        Rule A: total_active_minutes = completed_at - started_at
                delayed = total_active_minutes > delay_threshold
        """
        result = BuildMetricsResult()
        started_at = build.get('started_at')
        completed_at = build.get('completed_at')

        if started_at and completed_at:
            result.total_active_minutes = self._calculate_minutes(started_at, completed_at)
            result.delayed = result.total_active_minutes > self.config.delay_threshold_minutes

        return result

    def _process_in_progress(self, build: Dict[str, Any], now: datetime) -> BuildMetricsResult:
        """
        Process IN_PROGRESS build.
        Rule B: total_active_minutes = now - started_at
                delayed = total_active_minutes > delay_threshold
                stalled = (now - last_status_change) > stall_threshold
        """
        result = BuildMetricsResult()
        started_at = build.get('started_at')
        last_status_change = build.get('last_status_change')

        if started_at:
            result.total_active_minutes = self._calculate_minutes(started_at, now)
            result.delayed = result.total_active_minutes > self.config.delay_threshold_minutes

        if last_status_change:
            result.minutes_in_current_state = self._calculate_minutes(last_status_change, now)
            result.stalled = result.minutes_in_current_state > self.config.stall_threshold_minutes

        return result

    def _process_paused(self, build: Dict[str, Any], now: datetime) -> BuildMetricsResult:
        """
        Process PAUSED build.
        Rule C: total_paused_minutes = now - last_status_change
                stalled = total_paused_minutes > stall_threshold
        """
        result = BuildMetricsResult()
        last_status_change = build.get('last_status_change')

        if last_status_change:
            result.total_paused_minutes = self._calculate_minutes(last_status_change, now)
            result.stalled = result.total_paused_minutes > self.config.stall_threshold_minutes
            result.minutes_in_current_state = result.total_paused_minutes

        return result

    def _process_not_started(self, build: Dict[str, Any], now: datetime) -> BuildMetricsResult:
        """
        Process NOT_STARTED build.
        Rule D: No time accumulation, delayed = False, stalled = False
        """
        return BuildMetricsResult(delayed=False, stalled=False)

    def _enrich_build(self, build: Dict[str, Any], now: datetime) -> Dict[str, Any]:
        """Compute metrics for a single build and return enriched version."""
        status = build.get('status', 'NOT_STARTED')

        if status == 'COMPLETED':
            result = self._process_completed(build, now)
        elif status == 'IN_PROGRESS':
            result = self._process_in_progress(build, now)
        elif status == 'PAUSED':
            result = self._process_paused(build, now)
        else:  # NOT_STARTED or unknown
            result = self._process_not_started(build, now)

        enriched = dict(build)
        enriched['metrics'] = {
            'total_active_minutes': result.total_active_minutes,
            'total_paused_minutes': result.total_paused_minutes,
            'minutes_in_current_state': result.minutes_in_current_state,
            'delayed': result.delayed,
            'stalled': result.stalled
        }
        return enriched

    def _generate_summary(self, enriched_builds: List[Dict[str, Any]]) -> Dict[str, int]:
        """Generate system-wide summary from enriched builds."""
        summary = {
            'total_builds': len(enriched_builds),
            'not_started': 0,
            'in_progress': 0,
            'paused': 0,
            'completed': 0,
            'delayed': 0,
            'stalled': 0
        }

        for build in enriched_builds:
            status = build.get('status', 'NOT_STARTED')

            if status == 'NOT_STARTED':
                summary['not_started'] += 1
            elif status == 'IN_PROGRESS':
                summary['in_progress'] += 1
            elif status == 'PAUSED':
                summary['paused'] += 1
            elif status == 'COMPLETED':
                summary['completed'] += 1

            metrics = build.get('metrics', {})
            if metrics.get('delayed', False):
                summary['delayed'] += 1
            if metrics.get('stalled', False):
                summary['stalled'] += 1

        return summary

    def evaluate(
        self,
        builds: List[Dict[str, Any]],
        now: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a list of builds and return enriched builds with summary.

        Args:
            builds: List of build dicts with workorder_id, status, timestamps
            now: Current time for calculations (UTC). Uses utcnow() if not provided.

        Returns:
            Dict with 'builds' (enriched list) and 'summary' (system stats)
        """
        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        enriched_builds = [self._enrich_build(build, now) for build in builds]
        summary = self._generate_summary(enriched_builds)

        return {
            'builds': enriched_builds,
            'summary': summary
        }


def evaluate(builds: List[Dict[str, Any]], now: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Convenience function to evaluate builds with default configuration.

    Args:
        builds: List of build dicts
        now: Current time (UTC)

    Returns:
        Dict with 'builds' and 'summary'
    """
    analytics = BuildMetrics()
    return analytics.evaluate(builds, now)
