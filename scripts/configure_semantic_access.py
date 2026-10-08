from __future__ import annotations

import os

import psycopg2
from psycopg2 import sql


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "hotel")
DB_USER = os.getenv("DB_USER", "analytics")
DB_PASSWORD = os.getenv("DB_PASSWORD", "analytics")

DOMAIN_ACCESS = {
    "hotel_ops_reader": os.getenv("HOTEL_OPS_SCHEMA", "analytics_dev_ops"),
    "data_quality_reader": os.getenv("DATA_QUALITY_SCHEMA", "analytics_dev_dq"),
}


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def role_exists(cursor, role_name: str) -> bool:
    cursor.execute("select 1 from pg_roles where rolname = %s", (role_name,))
    return cursor.fetchone() is not None


def configure_role(cursor, role_name: str, schema_name: str) -> None:
    if not role_exists(cursor, role_name):
        cursor.execute(
            sql.SQL("create role {} nologin").format(sql.Identifier(role_name))
        )

    cursor.execute(
        sql.SQL("grant {} to current_user").format(sql.Identifier(role_name))
    )
    cursor.execute(
        sql.SQL("revoke all on schema {} from public").format(
            sql.Identifier(schema_name)
        )
    )
    cursor.execute(
        sql.SQL("revoke all on all tables in schema {} from public").format(
            sql.Identifier(schema_name)
        )
    )
    cursor.execute(
        sql.SQL("grant usage on schema {} to {}").format(
            sql.Identifier(schema_name),
            sql.Identifier(role_name),
        )
    )
    cursor.execute(
        sql.SQL("grant select on all tables in schema {} to {}").format(
            sql.Identifier(schema_name),
            sql.Identifier(role_name),
        )
    )
    cursor.execute(
        sql.SQL(
            "alter default privileges in schema {} "
            "grant select on tables to {}"
        ).format(
            sql.Identifier(schema_name),
            sql.Identifier(role_name),
        )
    )


def main():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            for role_name, schema_name in DOMAIN_ACCESS.items():
                configure_role(cursor, role_name, schema_name)

    for role_name, schema_name in DOMAIN_ACCESS.items():
        print(f"configured {role_name} -> {schema_name}")


if __name__ == "__main__":
    main()
