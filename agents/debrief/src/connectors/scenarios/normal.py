"""
Scenario: Normal Day
A mostly healthy factory floor with one minor issue.
Good for showing Corvus in a calm, advisory role.
"""
from connectors.base import BaseMESConnector


class NormalScenarioConnector(BaseMESConnector):

    def fetch_builds(self) -> list[dict]:
        return [
            {
                "build_id": "WO-NORM-001",
                "station_id": "ASSEMBLY-A1",
                "operator_id": "OP-JD001",
                "start_time": "2026-03-10T06:00:00",
                "planned_end": "2026-03-10T10:00:00",
                "needed_by_date": "2026-03-10T12:00:00",
                "target_quantity": 100,
                "completed_quantity": 100,
                "labor_hours": 3.5,
                "status": "Completed",
                "notes": "Full batch completed on schedule",
            },
            {
                "build_id": "WO-NORM-002",
                "station_id": "ASSEMBLY-A2",
                "operator_id": "OP-AS002",
                "start_time": "2026-03-10T07:00:00",
                "planned_end": "2026-03-10T11:00:00",
                "needed_by_date": "2026-03-10T13:00:00",
                "target_quantity": 80,
                "completed_quantity": 72,
                "labor_hours": 3.0,
                "status": "In Progress",
                "notes": "On track, minor rework on 8 units",
            },
            {
                "build_id": "WO-NORM-003",
                "station_id": "MACHINING-01",
                "operator_id": "OP-MK003",
                "start_time": "2026-03-10T06:30:00",
                "planned_end": "2026-03-10T10:30:00",
                "needed_by_date": "2026-03-10T12:00:00",
                "target_quantity": 60,
                "completed_quantity": 60,
                "labor_hours": 4.0,
                "status": "Completed",
                "notes": "Completed early",
            },
            {
                "build_id": "WO-NORM-004",
                "station_id": "PAINT-01",
                "operator_id": "OP-T004",
                "start_time": "2026-03-10T08:00:00",
                "planned_end": "2026-03-10T13:00:00",
                "needed_by_date": "2026-03-10T14:00:00",
                "target_quantity": 90,
                "completed_quantity": 45,
                "labor_hours": 2.5,
                "status": "In Progress",
                "notes": "Midway through batch, on schedule",
            },
            {
                "build_id": "WO-NORM-005",
                "station_id": "INSPECT-01",
                "operator_id": "OP-LR005",
                "start_time": "2026-03-10T13:00:00",
                "planned_end": "2026-03-10T17:00:00",
                "needed_by_date": "2026-03-10T18:00:00",
                "target_quantity": 50,
                "completed_quantity": 0,
                "labor_hours": 0.0,
                "status": "Pending",
                "notes": "Afternoon inspection queue — operator assigned",
            },
        ]

    def get_bottleneck_report(self) -> list[dict]:
        return []

    def get_at_risk_report(self) -> list[dict]:
        return []

    def get_efficiency_by_station(self) -> dict:
        return {}
