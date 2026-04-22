-- Factory Simulation Test Data
-- Creates a builds table with 8 work orders simulating a manufacturing environment

-- Create the builds table
CREATE TABLE IF NOT EXISTS builds (
    build_id TEXT PRIMARY KEY,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL
);

-- Clear any existing data
DELETE FROM builds;

-- Insert 8 work orders with varied start/end times
-- Simulating a factory with morning and afternoon shifts

-- Morning shift work orders (06:00 - 14:00)
INSERT INTO builds (build_id, start_time, end_time) VALUES
    ('WO-2026-001', '2026-02-22T06:00:00', '2026-02-22T08:30:00'),
    ('WO-2026-002', '2026-02-22T07:00:00', '2026-02-22T09:15:00'),
    ('WO-2026-003', '2026-02-22T08:00:00', '2026-02-22T11:00:00'),
    ('WO-2026-004', '2026-02-22T09:30:00', '2026-02-22T12:00:00');

-- Afternoon shift work orders (14:00 - 22:00)
INSERT INTO builds (build_id, start_time, end_time) VALUES
    ('WO-2026-005', '2026-02-22T14:00:00', '2026-02-22T16:30:00'),
    ('WO-2026-006', '2026-02-22T15:00:00', '2026-02-22T17:45:00'),
    ('WO-2026-007', '2026-02-22T16:00:00', '2026-02-22T19:00:00'),
    ('WO-2026-008', '2026-02-22T18:00:00', '2026-02-22T21:30:00');

-- Verify the data
SELECT * FROM builds;
