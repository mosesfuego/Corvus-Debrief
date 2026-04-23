"""SQLite MES connector with full MES schema support.

Supports station tracking, operator assignment, production metrics,
and status management for Manufacturing Execution System integration.
"""
import sqlite3
from connectors.base import BaseMESConnector


class SQLiteMESConnector(BaseMESConnector):
    """Connector for SQLite database with MES tracking."""

    def fetch_builds(self) -> list[dict]:
        """Fetch builds from SQLite database with full MES schema."""
        db_path = self.config.get("db_path", "")
        table_name = self.config.get("table_name", "builds")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Fetch all MES fields including generated fulfillment_pct
            cursor.execute(f"""
                SELECT build_id, station_id, operator_id, start_time, 
                       planned_end, needed_by_date, target_quantity, 
                       completed_quantity, labor_hours, fulfillment_pct, 
                       status, notes
                FROM {table_name}
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "build_id": row[0],
                    "station_id": row[1],
                    "operator_id": row[2],
                    "start_time": row[3],
                    "planned_end": row[4],
                    "needed_by_date": row[5],
                    "target_quantity": row[6],
                    "completed_quantity": row[7],
                    "labor_hours": row[8],
                    "fulfillment_pct": row[9],
                    "status": row[10],
                    "notes": row[11],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"[CORVUS] SQLite fetch error: {e}")
            return []

    def get_bottleneck_report(self) -> list[dict]:
        """List all Blocked work orders by station."""
        db_path = self.config.get("db_path", "")
        table_name = self.config.get("table_name", "builds")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"""
                SELECT build_id, station_id, operator_id, status, notes
                FROM {table_name}
                WHERE status = 'Blocked'
                ORDER BY station_id
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "build_id": row[0],
                    "station_id": row[1],
                    "operator_id": row[2],
                    "status": row[3],
                    "notes": row[4],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"[CORVUS] SQLite bottleneck report error: {e}")
            return []

    def get_at_risk_report(self) -> list[dict]:
        """List work orders where planned_end > needed_by_date."""
        db_path = self.config.get("db_path", "")
        table_name = self.config.get("table_name", "builds")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"""
                SELECT build_id, station_id, planned_end, needed_by_date,
                       target_quantity, completed_quantity, status
                FROM {table_name}
                WHERE planned_end > needed_by_date
                  AND status NOT IN ('Completed')
                ORDER BY needed_by_date
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "build_id": row[0],
                    "station_id": row[1],
                    "planned_end": row[2],
                    "needed_by_date": row[3],
                    "target_quantity": row[4],
                    "completed_quantity": row[5],
                    "status": row[6],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"[CORVUS] SQLite at-risk report error: {e}")
            return []

    def get_efficiency_by_station(self) -> list[dict]:
        """Calculate fulfillment percentage per station."""
        db_path = self.config.get("db_path", "")
        table_name = self.config.get("table_name", "builds")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"""
                SELECT station_id,
                       COUNT(*) as total_orders,
                       SUM(target_quantity) as total_target,
                       SUM(completed_quantity) as total_completed,
                       ROUND(SUM(completed_quantity) * 100.0 / 
                             NULLIF(SUM(target_quantity), 0), 2) as avg_fulfillment_pct,
                       ROUND(AVG(labor_hours), 2) as avg_labor_hours
                FROM {table_name}
                GROUP BY station_id
                ORDER BY avg_fulfillment_pct DESC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "station_id": row[0],
                    "total_orders": row[1],
                    "total_target": row[2],
                    "total_completed": row[3],
                    "avg_fulfillment_pct": row[4],
                    "avg_labor_hours": row[5],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"[CORVUS] SQLite efficiency report error: {e}")
            return []

    def update_completed_status(self) -> int:
        """Trigger auto-completion for orders meeting target.
        
        Returns number of rows updated.
        """
        db_path = self.config.get("db_path", "")
        table_name = self.config.get("table_name", "builds")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"""
                UPDATE {table_name}
                SET status = 'Completed'
                WHERE completed_quantity >= target_quantity
                  AND status != 'Completed'
            """)
            
            updated = cursor.rowcount
            conn.commit()
            conn.close()
            
            return updated
        except Exception as e:
            print(f"[CORVUS] SQLite completion update error: {e}")
            return 0
