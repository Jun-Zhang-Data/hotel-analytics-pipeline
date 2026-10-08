from __future__ import annotations

import hashlib
import os
from typing import Any

import psycopg2


def _connect():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "hotel"),
        user=os.getenv("DB_USER", "analytics"),
        password=os.getenv("DB_PASSWORD", "analytics"),
    )


def question_fingerprint(question: str) -> str:
    normalized = " ".join(question.strip().lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def record_query_run(
    *,
    query_run_id: str,
    question: str,
    parser: str,
    requested_domain: str,
    selected_domain: str | None,
    metric: str | None,
    access_role: str | None,
    execution_mode: str,
    status: str,
    row_count: int | None,
    duration_ms: int,
    error_type: str | None = None,
    error_message: str | None = None,
) -> bool:
    payload: dict[str, Any] = {
        "query_run_id": query_run_id,
        "question_fingerprint": question_fingerprint(question),
        "parser": parser,
        "requested_domain": requested_domain,
        "selected_domain": selected_domain,
        "metric": metric,
        "access_role": access_role,
        "execution_mode": execution_mode,
        "status": status,
        "row_count": row_count,
        "duration_ms": duration_ms,
        "error_type": error_type,
        "error_message": (error_message or "")[:500] or None,
    }

    try:
        with _connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    insert into ops.semantic_query_runs (
                        query_run_id,
                        question_fingerprint,
                        parser,
                        requested_domain,
                        selected_domain,
                        metric,
                        access_role,
                        execution_mode,
                        status,
                        row_count,
                        duration_ms,
                        error_type,
                        error_message,
                        completed_at
                    )
                    values (
                        %(query_run_id)s,
                        %(question_fingerprint)s,
                        %(parser)s,
                        %(requested_domain)s,
                        %(selected_domain)s,
                        %(metric)s,
                        %(access_role)s,
                        %(execution_mode)s,
                        %(status)s,
                        %(row_count)s,
                        %(duration_ms)s,
                        %(error_type)s,
                        %(error_message)s,
                        current_timestamp
                    )
                    """,
                    payload,
                )
        return True
    except psycopg2.Error:
        return False
