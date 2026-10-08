from __future__ import annotations

import os
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from semantic_api.answer_formatter import format_answer
from semantic_api.catalog import load_catalog
from semantic_api.sql_generator import generate_sql


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "hotel"),
        user=os.getenv("DB_USER", "analytics"),
        password=os.getenv("DB_PASSWORD", "analytics"),
    )


def run_semantic_query(
    query: dict[str, Any],
    catalog_path=None,
) -> dict[str, Any]:
    catalog = load_catalog(catalog_path) if catalog_path else load_catalog()
    sql, params = generate_sql(query, catalog)

    with get_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, params)
            rows = [dict(row) for row in cursor.fetchall()]

    return {
        "domain": catalog["domain"],
        "query": query,
        "sql": sql,
        "rows": rows,
        "answer": format_answer(query, rows, catalog),
    }
