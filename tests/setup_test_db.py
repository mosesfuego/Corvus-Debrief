#!/usr/bin/env python3
"""Create a test SQLite database with factory work order data.

Updated schema for MES tracker with real-time status, personnel,
and production efficiency metrics.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "test_factory.db")


def create_table(cursor):
    """Create the builds table with MES schema including generated fulfillment_pct."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS builds (
            build_id TEXT PRIMARY KEY,
            station_id TEXT NOT NULL,
            operator_id TEXT NOT NULL,
            start_time TEXT NOT NULL,
            planned_end TEXT NOT NULL,
            needed_by_date TEXT NOT NULL,
            target_quantity INTEGER NOT NULL,
            completed_quantity INTEGER DEFAULT 0,
            labor_hours REAL DEFAULT 0.0,
            fulfillment_pct REAL GENERATED ALWAYS AS 
                (CASE WHEN target_quantity > 0 
                      THEN (completed_quantity * 100.0 / target_quantity) 
                      ELSE 0 END) STORED,
            status TEXT DEFAULT 'Pending' 
                CHECK (status IN ('Pending', 'In Progress', 'Completed', 'Blocked', 'Paused')),
            notes TEXT
        )
    """)


def update_completed_status(conn):
    """Trigger-like update: mark orders as Completed if target met."""
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE builds 
        SET status = 'Completed'
        WHERE completed_quantity >= target_quantity 
          AND status != 'Completed'
    """)
    conn.commit()
    return cursor.rowcount


def populate_test_data(cursor):
    """Insert 8 diverse work orders simulating live factory floor."""
    
    work_orders = [
        # 2 Completed: High efficiency, met deadlines
        (
            "WO-2026-001", "ASSEMBLY-01", "OP-M001",
            "2026-02-22T06:00:00", "2026-02-22T10:00:00", "2026-02-22T12:00:00",
            100, 100, 3.5, "Completed", "On time, full batch"
        ),
        (
            "WO-2026-002", "ASSEMBLY-02", "OP-F002",
            "2026-02-22T07:00:00", "2026-02-22T09:00:00", "2026-02-22T10:00:00",
            200, 200, 4.0, "Completed", "Early completion"
        ),
        
        # 2 In Progress: Varying % fulfillment
        (
            "WO-2026-003", "MACHINING-01", "OP-M003",
            "2026-02-22T08:30:00", "2026-02-22T14:00:00", "2026-02-22T15:00:00",
            150, 100, 4.5, "In Progress", "Running ahead of schedule"
        ),
        (
            "WO-2026-004", "MACHINING-02", "OP-F004",
            "2026-02-22T09:00:00", "2026-02-22T16:00:00", "2026-02-22T18:00:00",
            80, 20, 2.0, "In Progress", "Slow start, needs attention"
        ),
        
        # 1 Blocked: Part shortage at welding station
        (
            "WO-2026-005", "WELD-01", "OP-M005",
            "2026-02-22T10:00:00", "2026-02-22T13:00:00", "2026-02-22T14:00:00",
            50, 15, 1.5, "Blocked", "Part shortage - awaiting rivets"
        ),
        
        # 1 Paused: Shift change
        (
            "WO-2026-006", "PAINT-01", "OP-F006",
            "2026-02-22T11:00:00", "2026-02-22T17:00:00", "2026-02-22T19:00:00",
            60, 30, 3.0, "Paused", "Shift change - resuming after lunch"
        ),
        
        # 2 Pending: Future afternoon shift work
        (
            "WO-2026-007", "ASSEMBLY-03", "OP-NOTASSIGNED",
            "2026-02-22T14:00:00", "2026-02-22T18:00:00", "2026-02-22T20:00:00",
            120, 0, 0.0, "Pending", "Afternoon shift - TBD operator"
        ),
        (
            "WO-2026-008", "INSPECT-01", "OP-NOTASSIGNED",
            "2026-02-22T16:00:00", "2026-02-22T22:00:00", "2026-02-22T23:00:00",
            40, 0, 0.0, "Pending", "Evening inspection batch"
        ),
    ]
    
    cursor.executemany("""
        INSERT INTO builds 
        (build_id, station_id, operator_id, start_time, planned_end, needed_by_date,
         target_quantity, completed_quantity, labor_hours, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, work_orders)
    
    return len(work_orders)


def get_bottleneck_report(conn):
    """List all Blocked work orders and their associated station_id."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT build_id, station_id, operator_id, status, notes
        FROM builds
        WHERE status = 'Blocked'
        ORDER BY station_id
    """)
    return cursor.fetchall()


def get_at_risk_report(conn):
    """List work orders where planned_end is later than needed_by_date."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT build_id, station_id, planned_end, needed_by_date, 
               target_quantity, completed_quantity, status
        FROM builds
        WHERE planned_end > needed_by_date
          AND status NOT IN ('Completed')
        ORDER BY needed_by_date
    """)
    return cursor.fetchall()


def get_efficiency_report(conn):
    """Calculate fulfillment percentage per station_id."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT station_id,
               COUNT(*) as total_orders,
               SUM(target_quantity) as total_target,
               SUM(completed_quantity) as total_completed,
               ROUND(SUM(completed_quantity) * 100.0 / NULLIF(SUM(target_quantity), 0), 2) as avg_fulfillment_pct,
               ROUND(AVG(labor_hours), 2) as avg_labor_hours
        FROM builds
        GROUP BY station_id
        ORDER BY avg_fulfillment_pct DESC
    """)
    return cursor.fetchall()


def display_results(conn, work_orders_count, auto_completed_count):
    """Display summary and analytical queries."""
    cursor = conn.cursor()
    
    print("-" * 60)
    print(f"✅ Database: {DB_PATH}")
    print(f"✅ Inserted: {work_orders_count} work orders")
    print(f"✅ Auto-completed: {auto_completed_count} orders (target met)")
    print("-" * 60)
    
    # Show all data
    print("\n📋 ALL WORK ORDERS:")
    print("-" * 80)
    cursor.execute("""
        SELECT build_id, station_id, status, target_qty, completed_qty, 
               fulfillment_pct, labor_hours, notes
        FROM (SELECT build_id, station_id, status, 
                     target_quantity as target_qty,
                     completed_quantity as completed_qty,
                     fulfillment_pct,
                     labor_hours,
                     notes
              FROM builds)
    """)
    print(f"{'ID':15} | {'Station':12} | {'Status':12} | {'Target':>6} | {'Done':>6} | {'Fill%':>5} | Notes")
    print("-" * 80)
    for row in cursor.fetchall():
        id_, station, status, target, done, fill, labor, notes = row
        print(f"{id_:15} | {station:12} | {status:12} | {target:>6} | {done:>6} | {fill:>5.1f} | {notes[:30]}")
    
    # Bottleneck Report
    print("\n🚧 BOTTLENECK REPORT (Blocked Work Orders):")
    print("-" * 60)
    blocked = get_bottleneck_report(conn)
    if blocked:
        for row in blocked:
            print(f"  {row[0]} @ {row[1]} ({row[3]}) - {row[4]}")
    else:
        print("  No blocked work orders.")
    
    # At-Risk Report
    print("\n⚠️ AT-RISK REPORT (Past Due):")
    print("-" * 80)
    at_risk = get_at_risk_report(conn)
    if at_risk:
        print(f"{'ID':15} | {'Station':12} | {'End':16} | {'Due':16} | {'Done':>6}/{':<6'.format('Target')}")
        for row in at_risk:
            print(f"  {row[0]:15} | {row[1]:12} | {row[2][:16]} | {row[3][:16]} | {row[6]}")
    else:
        print("  No at-risk work orders.")
    
    # Efficiency Report
    print("\n📊 EFFICIENCY REPORT (By Station):")
    print("-" * 80)
    efficiency = get_efficiency_report(conn)
    if efficiency:
        print(f"{'Station':15} | {'Orders':>6} | {'Target':>8} | {'Done':>8} | {'Fill%':>7} | {'Avg Hrs':>8}")
        print("-" * 80)
        for row in efficiency:
            station, orders, tgt, done, fill, labor = row
            print(f"  {station:15} | {orders:>6} | {tgt:>8} | {done:>8} | {fill:>7.1f} | {labor:>8.2f}")
    else:
        print("  No data available.")


def main():
    """Main entry point - create database and populate with test data."""
    # Remove existing database for clean slate
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"🗑️  Removed existing database: {DB_PATH}")
    
    # Connect and create tables
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    create_table(cursor)
    conn.commit()
    
    # Populate with test data
    count = populate_test_data(cursor)
    conn.commit()
    
    # Trigger auto-completion for any orders meeting target
    auto_completed = update_completed_status(conn)
    
    # Display results
    display_results(conn, count, auto_completed)
    
    conn.close()
    print("\n" + "=" * 60)
    print("✅ Test database ready!")
    print("\nTo use in config:")
    print('  "mes_type": "sqlite"')
    print('  "db_path": "tests/test_factory.db"')
    print('  "table_name": "builds"')
    print("=" * 60)


if __name__ == "__main__":
    main()
    
