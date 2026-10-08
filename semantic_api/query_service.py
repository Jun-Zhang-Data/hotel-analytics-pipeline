from __future__ import annotations

import os
from typing import Any

import psycopg2
from psycopg2 import sql
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


def _set_domain_role(cursor, catalog: dict[str, Any]) -> None:
    role_name = catalog.get("access_role")
    if not role_name:
        return

    cursor.execute(
        sql.SQL("set local role {}").format(sql.Identifier(role_name))
    )


def run_semantic_query(
    query: dict[str, Any],
    catalog: dict[str, Any] | None = None,
    catalog_path=None,
) -> dict[str, Any]:
    if catalog is None:
        catalog = load_catalog(catalog_path) if catalog_path else load_catalog()

    sql_text, params = generate_sql(query, catalog)

    with get_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            _set_domain_role(cursor, catalog)
            cursor.execute(sql_text, params)
            rows = [dict(row) for row in cursor.fetchall()]

    return {
        "domain": catalog["domain"],
        "access_role": catalog.get("access_role"),
        "query": query,
        "sql": sql_text,
        "rows": rows,
        "answer": format_answer(query, rows, catalog),
    }
