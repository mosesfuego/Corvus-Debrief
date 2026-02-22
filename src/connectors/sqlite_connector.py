"""SQLite MES connector."""
import sqlite3
from connectors.base import BaseMESConnector


class SQLiteMESConnector(BaseMESConnector):
    """Connector for SQLite database."""

    def fetch_builds(self) -> list[dict]:
        """Fetch builds from SQLite database."""
        db_path = self.config.get("db_path", "")
        table_name = self.config.get("table_name", "builds")

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT build_id, start_time, end_time FROM {table_name}"
            )
            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    "build_id": row[0],
                    "start_time": row[1],
                    "end_time": row[2],
                }
                for row in rows
            ]
        except Exception:
            return []
