import hashlib
import os
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
    "hotels": {
        "file": DATA_DIR / "hotels.csv",
        "business_key": "hotel_id",
        "columns": [
            "ingestion_id",
            "hotel_id",
            "hotel_name",
            "city",
            "source_updated_at",
            "source_file",
        ],
    },
    "bookings": {
        "file": DATA_DIR / "bookings.csv",
        "business_key": "booking_id",
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


def load_dataset(table_name, cfg):
    df = pd.read_csv(cfg["file"])
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
    rows = list(df[columns].itertuples(index=False, name=None))
    column_sql = ", ".join(columns)

    query = f"""
        INSERT INTO raw.{table_name}
        ({column_sql})
        VALUES %s
        ON CONFLICT (ingestion_id)
        DO NOTHING
    """

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            execute_values(cursor, query, rows)
        connection.commit()
        print(f"Loaded {table_name}: {len(rows)} source rows processed")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    for table_name, config in CONFIG.items():
        load_dataset(table_name, config)
