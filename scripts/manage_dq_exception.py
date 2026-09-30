import argparse
import os
import uuid

import psycopg2

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "hotel")
DB_USER = os.getenv("DB_USER", "analytics")
DB_PASSWORD = os.getenv("DB_PASSWORD", "analytics")

ALLOWED_STATUSES = ("ACKNOWLEDGED", "RESOLVED", "REPROCESSED")


def connect():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def record_action(exception_id: str, status: str, actor: str, note: str | None) -> str:
    action_id = str(uuid.uuid4())
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO ops.dq_exception_actions (
                action_id, exception_id, action_status, actor, note
            ) VALUES (%s, %s, %s, %s, %s)
            """,
            (action_id, exception_id, status, actor, note),
        )
    print(
        f"Recorded DQ exception action: exception_id={exception_id} "
        f"status={status} actor={actor} action_id={action_id}"
    )
    return action_id


def parse_args():
    parser = argparse.ArgumentParser(
        description="Record an append-only lifecycle action for a DQ exception"
    )
    parser.add_argument("--exception-id", required=True)
    parser.add_argument("--status", choices=ALLOWED_STATUSES, required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--note")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record_action(args.exception_id, args.status, args.actor, args.note)


if __name__ == "__main__":
    main()
