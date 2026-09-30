import argparse
import hashlib
import os
import uuid
from datetime import date
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "hotel")
DB_USER = os.getenv("DB_USER", "analytics")
DB_PASSWORD = os.getenv("DB_PASSWORD", "analytics")

CONFIG = {
    "bookings": {
        "file": DATA_DIR / "bookings.csv",
        "business_key": "booking_id",
        "backfill_field": "booking_date",
        "columns": [
            "ingestion_id",
            "booking_id",
            "source_system_code",
            "source_hotel_code",
            "guest_id",
            "booking_date",
            "check_in_date",
            "check_out_date",
            "status",
            "source_updated_at",
            "source_file",
        ],
    },
    "payments": {
        "file": DATA_DIR / "payments.csv",
        "business_key": "payment_id",
        "backfill_field": "source_updated_at",
        "columns": [
            "ingestion_id",
            "payment_id",
            "booking_id",
            "amount",
            "currency",
            "source_updated_at",
            "source_file",
        ],
    },
}


def make_ingestion_id(business_key, source_updated_at):
    value = f"{business_key}|{source_updated_at}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def filter_backfill(df, field, start_date, end_date):
    if not start_date and not end_date:
        return df

    dates = pd.to_datetime(df[field], errors="raise").dt.date
    mask = pd.Series(True, index=df.index)
    if start_date:
        mask &= dates >= start_date
    if end_date:
        mask &= dates <= end_date
    return df.loc[mask].copy()


def record_run_start(connection, run_id, dataset_name, source_rows, candidate_rows, start_date, end_date):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO ops.ingestion_runs (
                run_id, dataset_name, status, source_rows, candidate_rows,
                backfill_start, backfill_end
            ) VALUES (%s, %s, 'STARTED', %s, %s, %s, %s)
            """,
            (run_id, dataset_name, source_rows, candidate_rows, start_date, end_date),
        )
    connection.commit()


def record_run_end(connection, run_id, dataset_name, status, inserted_rows=0, duplicate_rows=0,
                   min_source_updated_at=None, max_source_updated_at=None, error_message=None):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE ops.ingestion_runs
            SET completed_at = CURRENT_TIMESTAMP,
                status = %s,
                inserted_rows = %s,
                duplicate_rows = %s,
                min_source_updated_at = %s,
                max_source_updated_at = %s,
                error_message = %s
            WHERE run_id = %s AND dataset_name = %s
            """,
            (
                status,
                inserted_rows,
                duplicate_rows,
                min_source_updated_at,
                max_source_updated_at,
                error_message,
                run_id,
                dataset_name,
            ),
        )
    connection.commit()


def load_dataset(table_name, cfg, run_id, start_date=None, end_date=None):
    source_df = pd.read_csv(cfg["file"])
    df = filter_backfill(source_df, cfg["backfill_field"], start_date, end_date)
    business_key = cfg["business_key"]

    df["ingestion_id"] = [
        make_ingestion_id(key, timestamp)
        for key, timestamp in zip(
            df[business_key].astype(str),
            df["source_updated_at"].astype(str),
        )
    ]
    df["source_file"] = cfg["file"].name

    columns = cfg["columns"]
    load_df = df[columns].astype(object).where(pd.notna(df[columns]), None)
    rows = list(load_df.itertuples(index=False, name=None))
    column_sql = ", ".join(columns)

    connection = get_connection()
    record_run_start(
        connection,
        run_id,
        table_name,
        len(source_df),
        len(rows),
        start_date,
        end_date,
    )

    try:
        with connection.cursor() as cursor:
            if rows:
                query = f"""
                    INSERT INTO raw.{table_name}
                    ({column_sql})
                    VALUES %s
                    ON CONFLICT (ingestion_id)
                    DO NOTHING
                    RETURNING ingestion_id
                """
                execute_values(cursor, query, rows)
                inserted_rows = cursor.rowcount
            else:
                inserted_rows = 0
        connection.commit()

        duplicate_rows = len(rows) - inserted_rows
        source_times = pd.to_datetime(df["source_updated_at"], errors="coerce") if not df.empty else None
        min_source_updated_at = source_times.min().to_pydatetime() if source_times is not None and source_times.notna().any() else None
        max_source_updated_at = source_times.max().to_pydatetime() if source_times is not None and source_times.notna().any() else None
        record_run_end(
            connection,
            run_id,
            table_name,
            "SUCCESS",
            inserted_rows,
            duplicate_rows,
            min_source_updated_at,
            max_source_updated_at,
        )
        print(
            f"Loaded {table_name}: candidate={len(rows)} inserted={inserted_rows} "
            f"duplicates_skipped={duplicate_rows} run_id={run_id}"
        )
    except Exception as exc:
        connection.rollback()
        record_run_end(connection, run_id, table_name, "FAILED", error_message=str(exc)[:2000])
        raise
    finally:
        connection.close()


def parse_args():
    parser = argparse.ArgumentParser(description="Idempotent raw loader with controlled backfill support")
    parser.add_argument("--dataset", choices=["all", *CONFIG.keys()], default="all")
    parser.add_argument("--start-date", type=date.fromisoformat)
    parser.add_argument("--end-date", type=date.fromisoformat)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()
    if args.start_date and args.end_date and args.start_date > args.end_date:
        parser.error("--start-date must be on or before --end-date")
    return args


if __name__ == "__main__":
    args = parse_args()
    run_id = args.run_id or str(uuid.uuid4())
    datasets = CONFIG.keys() if args.dataset == "all" else [args.dataset]
    for table_name in datasets:
        load_dataset(
            table_name,
            CONFIG[table_name],
            run_id,
            start_date=args.start_date,
            end_date=args.end_date,
        )
