"""CSV MES connector (mock implementation with full MES schema).

Simulates a real Manufacturing Execution System with station tracking,
operator assignment, production metrics, and status management.
"""
from connectors.base import BaseMESConnector


class CSVMESConnector(BaseMESConnector):
    """Mock connector for CSV-based MES with full tracking support."""

    def fetch_builds(self) -> list[dict]:
        """Return mock builds simulating live factory floor data."""
        return [
            {
                "build_id": "csv-001",
                "station_id": "ASSEMBLY-A1",
                "operator_id": "OP-JD001",
                "start_time": "2026-02-22T06:00:00",
                "planned_end": "2026-02-22T10:00:00",
                "needed_by_date": "2026-02-22T12:00:00",
                "target_quantity": 100,
                "completed_quantity": 100,
                "labor_hours": 3.5,
                "status": "Completed",
                "notes": "Batch completed on schedule",
            },
            {
                "build_id": "csv-002",
                "station_id": "ASSEMBLY-A2",
                "operator_id": "OP-AS002",
                "start_time": "2026-02-22T07:00:00",
                "planned_end": "2026-02-22T09:00:00",
                "needed_by_date": "2026-02-22T10:00:00",
                "target_quantity": 75,
                "completed_quantity": 45,
                "labor_hours": 2.0,
                "status": "In Progress",
                "notes": "Running slightly behind",
            },
            {
                "build_id": "csv-003",
                "station_id": "WELD-01",
                "operator_id": "OP-M003",
                "start_time": "2026-02-22T08:00:00",
                "planned_end": "2026-02-22T14:00:00",
                "needed_by_date": "2026-02-22T12:00:00",
                "target_quantity": 50,
                "completed_quantity": 10,
                "labor_hours": 1.0,
                "status": "Blocked",
                "notes": "Waiting on QA clearance",
            },
            {
                "build_id": "csv-004",
                "station_id": "PAINT-01",
                "operator_id": "OP-T004",
                "start_time": "2026-02-22T09:30:00",
                "planned_end": "2026-02-22T13:00:00",
                "needed_by_date": "2026-02-22T14:00:00",
                "target_quantity": 80,
                "completed_quantity": 40,
                "labor_hours": 2.5,
                "status": "Paused",
                "notes": "Shift break - resuming at 10:00",
            },
            {
                "build_id": "csv-005",
                "station_id": "INSPECT-01",
                "operator_id": "OP-NOTASSIGNED",
                "start_time": "2026-02-22T14:00:00",
                "planned_end": "2026-02-22T18:00:00",
                "needed_by_date": "2026-02-22T20:00:00",
                "target_quantity": 60,
                "completed_quantity": 0,
                "labor_hours": 0.0,
                "status": "Pending",
                "notes": "Afternoon shift inspection queue",
            },
        ]

    def get_bottleneck_report(self) -> list[dict]:
        """Return blocked work orders by station."""
        return [
            build for build in self.fetch_builds()
            if build.get("status") == "Blocked"
        ]

    def get_at_risk_report(self) -> list[dict]:
        """Return work orders where planned_end > needed_by_date."""
        at_risk = []
        for build in self.fetch_builds():
            planned_end = build.get("planned_end", "")
            needed_by = build.get("needed_by_date", "")
            status = build.get("status", "")
            if planned_end and needed_by and planned_end > needed_by and status != "Completed":
                at_risk.append(build)
        return at_risk

    def get_efficiency_by_station(self) -> dict:
        """Calculate fulfillment percentage per station."""
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
        
        efficiency = {}
        for station, stats in station_stats.items():
            target = stats["total_target"]
            completed = stats["total_completed"]
            efficiency[station] = {
                "fulfillment_pct": (completed / target * 100) if target > 0 else 0,
                "labor_hours": stats["labor_hours"],
                "order_count": stats["order_count"]
            }
        
        return efficiency
