"""
Scenario: Crisis
Multiple blocked work orders, missed deadlines, cascading delays.
Good for showing Corvus under pressure — this is where it shines.
"""
from connectors.base import BaseMESConnector


class CrisisScenarioConnector(BaseMESConnector):

    def fetch_builds(self) -> list[dict]:
        return [
            {
                "build_id": "WO-CRIS-001",
                "station_id": "ASSEMBLY-A1",
                "operator_id": "OP-JD001",
                "start_time": "2026-03-10T06:00:00",
                "planned_end": "2026-03-10T09:00:00",
                "needed_by_date": "2026-03-10T08:00:00",
                "target_quantity": 200,
                "completed_quantity": 40,
                "labor_hours": 3.0,
                "status": "Blocked",
                "notes": "Conveyor belt fault — maintenance called, ETA unknown",
            },
            {
                "build_id": "WO-CRIS-002",
                "station_id": "WELD-01",
                "operator_id": "OP-WR002",
                "start_time": "2026-03-10T06:00:00",
                "planned_end": "2026-03-10T10:00:00",
                "needed_by_date": "2026-03-10T09:00:00",
                "target_quantity": 150,
                "completed_quantity": 30,
                "labor_hours": 4.0,
                "status": "Blocked",
                "notes": "Awaiting QA sign-off on weld spec deviation",
            },
            {
                "build_id": "WO-CRIS-003",
                "station_id": "MACHINING-01",
                "operator_id": "OP-MK003",
                "start_time": "2026-03-10T05:00:00",
                "planned_end": "2026-03-10T11:00:00",
                "needed_by_date": "2026-03-10T09:00:00",
                "target_quantity": 100,
                "completed_quantity": 20,
                "labor_hours": 6.0,
                "status": "In Progress",
                "notes": "Running 2 hours behind — tooling change took longer than expected",
            },
            {
                "build_id": "WO-CRIS-004",
                "station_id": "PAINT-01",
                "operator_id": "OP-T004",
                "start_time": "2026-03-10T07:00:00",
                "planned_end": "2026-03-10T12:00:00",
                "needed_by_date": "2026-03-10T10:00:00",
                "target_quantity": 80,
                "completed_quantity": 10,
                "labor_hours": 2.0,
                "status": "Paused",
                "notes": "Paint supply low — waiting on materials delivery",
            },
            {
                "build_id": "WO-CRIS-005",
                "station_id": "INSPECT-01",
                "operator_id": "OP-NOTASSIGNED",
                "start_time": "2026-03-10T12:00:00",
                "planned_end": "2026-03-10T16:00:00",
                "needed_by_date": "2026-03-10T14:00:00",
                "target_quantity": 60,
                "completed_quantity": 0,
                "labor_hours": 0.0,
                "status": "Pending",
                "notes": "Downstream inspection will bottleneck if upstream clears",
            },
        ]

    def get_bottleneck_report(self) -> list[dict]:
        return [
            b for b in self.fetch_builds()
            if b["status"] == "Blocked"
        ]

    def get_at_risk_report(self) -> list[dict]:
        at_risk = []
        for build in self.fetch_builds():
            if (build["planned_end"] > build["needed_by_date"]
                    and build["status"] != "Completed"):
                at_risk.append(build)
        return at_risk

    def get_efficiency_by_station(self) -> dict:
        return {}
