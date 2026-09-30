CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS analytics_dev;
CREATE SCHEMA IF NOT EXISTS analytics_prod;
CREATE SCHEMA IF NOT EXISTS ops;

CREATE TABLE IF NOT EXISTS raw.bookings (
    ingestion_id TEXT PRIMARY KEY,
    booking_id TEXT NOT NULL,
    source_system_code TEXT,
    source_hotel_code TEXT,
    guest_id TEXT,
    booking_date TEXT,
    check_in_date TEXT,
    check_out_date TEXT,
    status TEXT,
    source_updated_at TIMESTAMP NOT NULL,
    source_file TEXT,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.payments (
    ingestion_id TEXT PRIMARY KEY,
    payment_id TEXT NOT NULL,
    booking_id TEXT,
    amount NUMERIC,
    currency TEXT,
    source_updated_at TIMESTAMP NOT NULL,
    source_file TEXT,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ops.ingestion_runs (
    run_id TEXT NOT NULL,
    dataset_name TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT NOT NULL,
    source_rows INTEGER NOT NULL DEFAULT 0,
    candidate_rows INTEGER NOT NULL DEFAULT 0,
    inserted_rows INTEGER NOT NULL DEFAULT 0,
    duplicate_rows INTEGER NOT NULL DEFAULT 0,
    min_source_updated_at TIMESTAMP,
    max_source_updated_at TIMESTAMP,
    backfill_start DATE,
    backfill_end DATE,
    error_message TEXT,
    PRIMARY KEY (run_id, dataset_name),
    CONSTRAINT ingestion_runs_status_chk CHECK (status IN ('STARTED', 'SUCCESS', 'FAILED'))
);

CREATE INDEX IF NOT EXISTS idx_ingestion_runs_dataset_completed
    ON ops.ingestion_runs (dataset_name, completed_at DESC);

CREATE TABLE IF NOT EXISTS ops.dq_exception_actions (
    action_id UUID PRIMARY KEY,
    exception_id TEXT NOT NULL,
    action_status TEXT NOT NULL,
    actor TEXT NOT NULL,
    note TEXT,
    action_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT dq_exception_actions_status_chk
        CHECK (action_status IN ('ACKNOWLEDGED', 'RESOLVED', 'REPROCESSED'))
);

CREATE INDEX IF NOT EXISTS idx_dq_exception_actions_exception_time
    ON ops.dq_exception_actions (exception_id, action_at DESC);
