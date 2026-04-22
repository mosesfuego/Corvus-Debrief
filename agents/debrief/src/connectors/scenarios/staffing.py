"""
Scenario: Staffing Disaster
Multiple unassigned operators, shift gaps, work piling up.
Good for showing Corvus's scheduling intelligence.
"""
from connectors.base import BaseMESConnector


class StaffingScenarioConnector(BaseMESConnector):

    def fetch_builds(self) -> list[dict]:
        return [
            {
                "build_id": "WO-STAF-001",
                "station_id": "ASSEMBLY-A1",
                "operator_id": "OP-JD001",
                "start_time": "2026-03-10T06:00:00",
                "planned_end": "2026-03-10T10:00:00",
                "needed_by_date": "2026-03-10T11:00:00",
                "target_quantity": 100,
                "completed_quantity": 100,
                "labor_hours": 4.0,
                "status": "Completed",
                "notes": "Day shift completed successfully",
            },
            {
                "build_id": "WO-STAF-002",
                "station_id": "ASSEMBLY-A2",
                "operator_id": "OP-NOTASSIGNED",
                "start_time": "2026-03-10T14:00:00",
                "planned_end": "2026-03-10T18:00:00",
                "needed_by_date": "2026-03-10T18:00:00",
                "target_quantity": 120,
                "completed_quantity": 0,
                "labor_hours": 0.0,
                "status": "Pending",
                "notes": "Afternoon shift — no operator assigned",
            },
            {
                "build_id": "WO-STAF-003",
                "station_id": "WELD-01",
                "operator_id": "OP-NOTASSIGNED",
                "start_time": "2026-03-10T15:00:00",
                "planned_end": "2026-03-10T19:00:00",
                "needed_by_date": "2026-03-10T18:00:00",
                "target_quantity": 80,
                "completed_quantity": 0,
                "labor_hours": 0.0,
                "status": "Pending",
                "notes": "Evening weld batch — certified welder called out sick",
            },
            {
                "build_id": "WO-STAF-004",
                "station_id": "MACHINING-01",
                "operator_id": "OP-NOTASSIGNED",
                "start_time": "2026-03-10T22:00:00",
                "planned_end": "2026-03-11T06:00:00",
                "needed_by_date": "2026-03-11T07:00:00",
                "target_quantity": 200,
                "completed_quantity": 0,
                "labor_hours": 0.0,
                "status": "Pending",
                "notes": "Night shift machining — entire crew unconfirmed",
            },
            {
                "build_id": "WO-STAF-005",
                "station_id": "INSPECT-01",
                "operator_id": "OP-LR005",
                "start_time": "2026-03-10T08:00:00",
                "planned_end": "2026-03-10T12:00:00",
                "needed_by_date": "2026-03-10T13:00:00",
                "target_quantity": 60,
                "completed_quantity": 55,
                "labor_hours": 3.5,
                "status": "In Progress",
                "notes": "Day shift inspection nearly complete",
            },
        ]

    def get_bottleneck_report(self) -> list[dict]:
        return []

    def get_at_risk_report(self) -> list[dict]:
        return [
            b for b in self.fetch_builds()
            if b.get("operator_id") == "OP-NOTASSIGNED"
            and b["status"] != "Completed"
        ]

    def get_efficiency_by_station(self) -> dict:
        return {}
