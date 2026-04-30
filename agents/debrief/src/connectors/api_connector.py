"""API MES connector (mock implementation)."""
from connectors.base import BaseMESConnector


class APIMESConnector(BaseMESConnector):
    """Mock connector for API-based MES."""

    def fetch_builds(self) -> list[dict]:
        """Return hardcoded mock builds."""
        return [
            {
                "build_id": "api-001",
                "station_id": "API-ASSEMBLY-01",
                "operator_id": "OP-API-001",
                "start_time": "2026-02-20T08:00:00",
                "planned_end": "2026-02-20T10:00:00",
                "needed_by_date": "2026-02-20T11:00:00",
                "target_quantity": 100,
                "completed_quantity": 65,
                "labor_hours": 1.5,
                "status": "In Progress",
                "notes": "Mock API build running normally",
            },
            {
                "build_id": "api-002",
                "station_id": "API-KITTING-01",
                "operator_id": "OP-API-002",
                "start_time": "2026-02-20T11:00:00",
                "planned_end": "2026-02-20T13:00:00",
                "needed_by_date": "2026-02-20T12:30:00",
                "target_quantity": 40,
                "completed_quantity": 0,
                "labor_hours": 0.5,
                "status": "Blocked",
                "notes": "Mock API build awaiting material release",
            },
        ]
