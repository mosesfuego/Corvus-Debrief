"""API MES connector (mock implementation)."""
from connectors.base import BaseMESConnector


class APIMESConnector(BaseMESConnector):
    """Mock connector for API-based MES."""

    def fetch_builds(self) -> list[dict]:
        """Return hardcoded mock builds."""
        return [
            {
                "build_id": "api-001",
                "start_time": "2026-02-20T08:00:00",
                "end_time": "2026-02-20T10:00:00",
            },
            {
                "build_id": "api-002",
                "start_time": "2026-02-20T11:00:00",
                "end_time": "2026-02-20T13:00:00",
            },
        ]
