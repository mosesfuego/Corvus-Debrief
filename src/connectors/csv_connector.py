"""CSV MES connector (mock implementation)."""
from connectors.base import BaseMESConnector


class CSVMESConnector(BaseMESConnector):
    """Mock connector for CSV-based MES."""

    def fetch_builds(self) -> list[dict]:
        """Return hardcoded mock builds."""
        return [
            {
                "build_id": "csv-001",
                "start_time": "2026-02-19T09:00:00",
                "end_time": "2026-02-19T11:30:00",
            },
            {
                "build_id": "csv-002",
                "start_time": "2026-02-19T14:00:00",
                "end_time": "2026-02-19T16:00:00",
            },
        ]
