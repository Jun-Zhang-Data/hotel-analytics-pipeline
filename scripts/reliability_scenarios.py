import argparse
import os
from pathlib import Path

import pandas as pd
import psycopg2

ROOT = Path(__file__).resolve().parents[1]
BOOKINGS_PATH = ROOT / "data" / "bookings.csv"

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "hotel")
DB_USER = os.getenv("DB_USER", "analytics")
DB_PASSWORD = os.getenv("DB_PASSWORD", "analytics")
TARGET_SCHEMA = os.getenv("TARGET_SCHEMA", "analytics_dev")

LATE_ARRIVAL = {
    "booking_id": "B001",
    "source_system_code": "PMS_A",
    "source_hotel_code": "STO01",
    "guest_id": "G001",
    "booking_date": "2026-09-01",
    "check_in_date": "2026-09-10",
    "check_out_date": "2026-09-12",
    "status": "CANCELLED",
    "source_updated_at": "2026-09-03 10:00:00",
}

HISTORICAL_CORRECTION = {
    "booking_id": "B003",
    "source_system_code": "PMS_A",
    "source_hotel_code": "GOT01",
    "guest_id": "G003",
    "booking_date": "2026-09-01",
    "check_in_date": "2026-09-08",
    "check_out_date": "2026-09-10",
    "status": "CONFIRMED",
    "source_updated_at": "2026-09-04 12:00:00",
}


def connect():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def append_booking(row: dict) -> None:
    df = pd.read_csv(BOOKINGS_PATH)
    duplicate = (
        df["booking_id"].astype(str).eq(row["booking_id"])
        & df["source_updated_at"].astype(str).eq(row["source_updated_at"])
    )
    if duplicate.any():
        print(
            f"Scenario row already present: {row['booking_id']} "
            f"at {row['source_updated_at']}"
        )
        return

    updated = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    updated.to_csv(BOOKINGS_PATH, index=False)
    print(
        f"Appended scenario row: {row['booking_id']} "
        f"at {row['source_updated_at']}"
    )


def query_one(sql: str, params=None):
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchone()


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")
    print(f"PASS {label}: {actual!r}")


def assert_ingestion_run(run_id: str, expected_inserted: int) -> None:
    row = query_one(
        """
        SELECT inserted_rows, status
        FROM ops.ingestion_runs
        WHERE run_id = %s AND dataset_name = 'bookings'
        """,
        (run_id,),
    )
    if row is None:
        raise AssertionError(f"No bookings ingestion metadata found for run_id={run_id}")
    assert_equal(row[0], expected_inserted, f"{run_id} inserted_rows")
    assert_equal(row[1], "SUCCESS", f"{run_id} status")


def assert_late_arrival() -> None:
    raw_versions = query_one(
        "SELECT count(*) FROM raw.bookings WHERE booking_id = 'B001'"
    )[0]
    assert_equal(raw_versions, 2, "B001 raw versions after late arrival")

    trusted = query_one(
        f"""
        SELECT booking_status, count(*) OVER ()
        FROM {TARGET_SCHEMA}.fct_bookings
        WHERE booking_id = 'B001'
        """
    )
    if trusted is None:
        raise AssertionError("B001 missing from trusted fact after late-arriving update")
    assert_equal(trusted[0], "CANCELLED", "B001 latest status in trusted fact")
    assert_equal(trusted[1], 1, "B001 trusted-row count")
    assert_ingestion_run("ci-late-arrival", 1)


def assert_historical_correction() -> None:
    raw_versions = query_one(
        "SELECT count(*) FROM raw.bookings WHERE booking_id = 'B003'"
    )[0]
    assert_equal(raw_versions, 2, "B003 raw versions after historical correction")

    trusted = query_one(
        f"""
        SELECT check_out_date::text, count(*) OVER ()
        FROM {TARGET_SCHEMA}.fct_bookings
        WHERE booking_id = 'B003'
        """
    )
    if trusted is None:
        raise AssertionError("B003 missing from trusted fact after historical correction")
    assert_equal(trusted[0], "2026-09-10", "B003 corrected check_out_date")
    assert_equal(trusted[1], 1, "B003 trusted-row count")
    assert_ingestion_run("ci-historical-correction", 1)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create and verify deterministic production-reliability scenarios"
    )
    parser.add_argument(
        "action",
        choices=[
            "append-late-arrival",
            "append-historical-correction",
            "assert-late-arrival",
            "assert-historical-correction",
        ],
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.action == "append-late-arrival":
        append_booking(LATE_ARRIVAL)
    elif args.action == "append-historical-correction":
        append_booking(HISTORICAL_CORRECTION)
    elif args.action == "assert-late-arrival":
        assert_late_arrival()
    elif args.action == "assert-historical-correction":
        assert_historical_correction()


if __name__ == "__main__":
    main()
