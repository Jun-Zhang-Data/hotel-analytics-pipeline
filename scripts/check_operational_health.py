import json
import os
from datetime import datetime, timezone

import psycopg2

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "hotel")
DB_USER = os.getenv("DB_USER", "analytics")
DB_PASSWORD = os.getenv("DB_PASSWORD", "analytics")
TARGET_SCHEMA = os.getenv("TARGET_SCHEMA", "analytics_dev")

FRESHNESS_WARNING_HOURS = float(os.getenv("FRESHNESS_WARNING_HOURS", "36"))
FRESHNESS_BLOCKING_HOURS = float(os.getenv("FRESHNESS_BLOCKING_HOURS", "72"))
DQ_WARNING_PASS_RATE = float(os.getenv("DQ_WARNING_PASS_RATE", "0.95"))
DQ_BLOCKING_PASS_RATE = float(os.getenv("DQ_BLOCKING_PASS_RATE", "0.80"))
MAPPING_WARNING_RATE = float(os.getenv("MAPPING_WARNING_RATE", "0.98"))
MAPPING_BLOCKING_RATE = float(os.getenv("MAPPING_BLOCKING_RATE", "0.90"))
VOLUME_CHANGE_WARNING_PCT = float(os.getenv("VOLUME_CHANGE_WARNING_PCT", "0.50"))


def connect():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def query_one(cursor, sql, params=None):
    cursor.execute(sql, params or ())
    return cursor.fetchone()


def classify(value, warning_threshold, blocking_threshold, lower_is_worse=True):
    if lower_is_worse:
        if value < blocking_threshold:
            return "BLOCKING"
        if value < warning_threshold:
            return "WARNING"
    else:
        if value > blocking_threshold:
            return "BLOCKING"
        if value > warning_threshold:
            return "WARNING"
    return "OK"


def main():
    checks = []
    now = datetime.now(timezone.utc)

    with connect() as connection, connection.cursor() as cursor:
        latest_source = query_one(
            cursor,
            "SELECT max(source_updated_at) FROM raw.bookings",
        )[0]
        if latest_source is None:
            checks.append({"check": "bookings_freshness", "severity": "BLOCKING", "detail": "raw.bookings is empty"})
        else:
            if latest_source.tzinfo is None:
                latest_source = latest_source.replace(tzinfo=timezone.utc)
            age_hours = (now - latest_source).total_seconds() / 3600
            severity = classify(age_hours, FRESHNESS_WARNING_HOURS, FRESHNESS_BLOCKING_HOURS, lower_is_worse=False)
            checks.append({"check": "bookings_freshness", "severity": severity, "value": round(age_hours, 2), "unit": "hours"})

        dq = query_one(
            cursor,
            f"""
            SELECT
                sum(records_passed)::numeric / nullif(sum(records_checked), 0),
                sum(records_failed)
            FROM {TARGET_SCHEMA}.fct_data_quality_results
            """,
        )
        dq_pass_rate = float(dq[0]) if dq and dq[0] is not None else 0.0
        dq_failed = int(dq[1] or 0) if dq else 0
        checks.append({
            "check": "dq_pass_rate",
            "severity": classify(dq_pass_rate, DQ_WARNING_PASS_RATE, DQ_BLOCKING_PASS_RATE),
            "value": round(dq_pass_rate, 4),
            "failed_records": dq_failed,
        })

        mapping = query_one(
            cursor,
            f"""
            SELECT sum(records_passed)::numeric / nullif(sum(records_checked), 0)
            FROM {TARGET_SCHEMA}.fct_data_quality_results
            WHERE quality_dimension = 'MAPPING_COVERAGE'
            """,
        )[0]
        mapping_rate = float(mapping) if mapping is not None else 0.0
        checks.append({
            "check": "mapping_coverage",
            "severity": classify(mapping_rate, MAPPING_WARNING_RATE, MAPPING_BLOCKING_RATE),
            "value": round(mapping_rate, 4),
        })

        run_rows = query_one(
            cursor,
            """
            WITH ranked AS (
                SELECT candidate_rows,
                       row_number() OVER (ORDER BY completed_at DESC) AS rn
                FROM ops.ingestion_runs
                WHERE dataset_name = 'bookings' AND status = 'SUCCESS'
            )
            SELECT
                max(candidate_rows) FILTER (WHERE rn = 1),
                max(candidate_rows) FILTER (WHERE rn = 2)
            FROM ranked
            WHERE rn <= 2
            """,
        )
        latest_rows, previous_rows = run_rows
        if latest_rows is not None and previous_rows not in (None, 0):
            change = abs(latest_rows - previous_rows) / previous_rows
            severity = "WARNING" if change > VOLUME_CHANGE_WARNING_PCT else "OK"
            checks.append({"check": "booking_volume_change", "severity": severity, "value": round(change, 4)})
        else:
            checks.append({"check": "booking_volume_change", "severity": "INFO", "detail": "insufficient successful runs for comparison"})

        failed_run = query_one(
            cursor,
            """
            SELECT count(*)
            FROM ops.ingestion_runs
            WHERE status = 'FAILED'
              AND started_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
            """,
        )[0]
        checks.append({
            "check": "failed_ingestions_24h",
            "severity": "WARNING" if failed_run else "OK",
            "value": int(failed_run),
        })

    blocking = [check for check in checks if check["severity"] == "BLOCKING"]
    warnings = [check for check in checks if check["severity"] == "WARNING"]
    payload = {
        "checked_at": now.isoformat(),
        "target_schema": TARGET_SCHEMA,
        "overall_status": "BLOCKING" if blocking else ("WARNING" if warnings else "OK"),
        "checks": checks,
    }
    print(json.dumps(payload, indent=2, default=str))

    if blocking:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
