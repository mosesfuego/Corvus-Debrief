"""Base MES connector abstract class."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class BaseMESConnector(ABC):
    """Abstract base class for MES connectors.
    
    Supports full Manufacturing Execution System schema with:
    - Station tracking (station_id)
    - Operator assignment (operator_id)
    - Production metrics (target/completed quantity, labor hours)
    - Status management (Pending, In Progress, Completed, Blocked, Paused)
    - Fulfillment tracking
    """

    def __init__(self, config: dict):
        """Initialize connector with configuration."""
        self.config = config

    @abstractmethod
    def fetch_builds(self) -> list[dict]:
        """Fetch builds from MES system.
        
        Returns: List of dictionaries with keys:
            - build_id (str): Unique work order identifier
            - station_id (str): Workstation/station identifier
            - operator_id (str): Assigned operator identifier
            - start_time (str): ISO8601 start timestamp
            - planned_end (str): ISO8601 planned completion timestamp
            - needed_by_date (str): ISO8601 customer deadline
            - target_quantity (int): Total units required
            - completed_quantity (int): Units finished (default 0)
            - labor_hours (float): Total man-hours spent
            - fulfillment_pct (float): Computed completion percentage
            - status (str): One of ['Pending', 'In Progress', 'Completed', 'Blocked', 'Paused']
            - notes (str): Optional notes/comments
        """
        pass

    def get_bottleneck_report(self) -> list[dict]:
        """Get blocked work orders by station.
        
        Optional: Override for direct database efficiency.
        Base implementation filters fetched builds.
        """
        return [
            build for build in self.fetch_builds()
            if build.get("status") == "Blocked"
        ]

    def get_at_risk_report(self) -> list[dict]:
        """Get work orders where planned_end > needed_by_date.
        
        Optional: Override for direct database efficiency.
        Base implementation filters fetched builds.
        """
        at_risk = []
        for build in self.fetch_builds():
            status = build.get("status", "")
            if status != "Completed" and self._is_late(build):
                at_risk.append(build)
        return at_risk

    def _is_late(self, build: dict) -> bool:
        planned = self._parse_dt(build.get("planned_end"))
        needed = self._parse_dt(build.get("needed_by_date"))
        return bool(planned and needed and planned > needed)

    @staticmethod
    def _parse_dt(value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value))
        except ValueError:
            return None

    def get_efficiency_by_station(self) -> list[dict]:
        """Calculate fulfillment percentage per station.
        
        Optional: Override for direct database efficiency.
        Base implementation computes from fetched builds.
        """
        from collections import defaultdict
        
        station_stats = defaultdict(lambda: {
            "total_target": 0,
            "total_completed": 0,
            "labor_hours": 0.0,
            "order_count": 0
        })
        
        for build in self.fetch_builds():
            station = build.get("station_id", "UNKNOWN")
            station_stats[station]["total_target"] += build.get("target_quantity", 0)
            station_stats[station]["total_completed"] += build.get("completed_quantity", 0)
            station_stats[station]["labor_hours"] += build.get("labor_hours", 0.0)
            station_stats[station]["order_count"] += 1
        
        efficiency = []
        for station, stats in station_stats.items():
            target = stats["total_target"]
            completed = stats["total_completed"]
            efficiency.append({
                "station_id": station,
                "total_orders": stats["order_count"],
                "total_target": target,
                "total_completed": completed,
                "avg_fulfillment_pct": round((completed / target * 100), 2) if target > 0 else 0,
                "avg_labor_hours": round(stats["labor_hours"] / max(stats["order_count"], 1), 2),
            })
        
        # Sort by fulfillment percentage descending
        efficiency.sort(key=lambda x: x["avg_fulfillment_pct"], reverse=True)
        return efficiency
