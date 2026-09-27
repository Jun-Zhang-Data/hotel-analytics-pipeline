CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS analytics_dev;
CREATE SCHEMA IF NOT EXISTS analytics_prod;

CREATE TABLE IF NOT EXISTS raw.hotels (
    ingestion_id TEXT PRIMARY KEY,
    hotel_id TEXT NOT NULL,
    hotel_name TEXT,
    city TEXT,
    source_updated_at TIMESTAMP NOT NULL,
    source_file TEXT,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.bookings (
    ingestion_id TEXT PRIMARY KEY,
    booking_id TEXT NOT NULL,
    hotel_id TEXT,
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
