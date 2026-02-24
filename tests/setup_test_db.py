#!/usr/bin/env python3
"""Create a test SQLite database with factory work order data."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "test_factory.db")

# Connect to database (creates if not exists)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create the builds table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS builds (
        build_id TEXT PRIMARY KEY,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL
    )
""")

# Clear any existing data
cursor.execute("DELETE FROM builds")

# Work orders simulating a factory with morning and afternoon shifts
work_orders = [
    # Morning shift work orders (06:00 - 14:00)
    ("WO-2026-001", "2026-02-22T06:00:00", "2026-02-22T08:30:00"),
    ("WO-2026-002", "2026-02-22T07:00:00", "2026-02-22T09:15:00"),
    ("WO-2026-003", "2026-02-22T08:00:00", "2026-02-22T11:00:00"),
    ("WO-2026-004", "2026-02-22T09:30:00", "2026-02-22T12:00:00"),
    # Afternoon shift work orders (14:00 - 22:00)
    ("WO-2026-005", "2026-02-22T14:00:00", "2026-02-22T16:30:00"),
    ("WO-2026-006", "2026-02-22T15:00:00", "2026-02-22T17:45:00"),
    ("WO-2026-007", "2026-02-22T16:00:00", "2026-02-22T19:00:00"),
    ("WO-2026-008", "2026-02-22T18:00:00", "2026-02-22T21:30:00"),
]

cursor.executemany(
    "INSERT INTO builds (build_id, start_time, end_time) VALUES (?, ?, ?)",
    work_orders
)

conn.commit()

# Verify the data
print(f"Created test database: {DB_PATH}")
print(f"\nInserted {len(work_orders)} work orders:")
print("-" * 50)

cursor.execute("SELECT build_id, start_time, end_time FROM builds")
for row in cursor.fetchall():
    print(f"  {row[0]:15} | {row[1][:16]} → {row[2][:16]}")

conn.close()
print("-" * 50)
print("\n✅ Test database ready!")
print(f"\nTo use in config:")
print(f'  "mes_type": "sqlite"')
print(f'  "db_path": "tests/test_factory.db"')
print(f'  "table_name": "builds"')
