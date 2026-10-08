from __future__ import annotations

from typing import Any

from semantic_api.catalog import resolve_source_relation
from semantic_api.validator import validate_query


def generate_sql(
    query: dict[str, Any],
    catalog: dict[str, Any],
) -> tuple[str, list[Any]]:
    validated = validate_query(query, catalog)

    metric_name = validated["metric"]
    metric_expression = catalog["metrics"][metric_name]["expression"]
    dimension_names = validated["dimensions"]
    dimension_columns = [
        catalog["dimensions"][name]["column"] for name in dimension_names
    ]

    select_parts = [*dimension_columns, f"{metric_expression} as {metric_name}"]
    sql_parts = [
        "select",
        "    " + ",\n    ".join(select_parts),
        f"from {resolve_source_relation(catalog)}",
    ]

    where_clauses: list[str] = []
    params: list[Any] = []

    time_dimension_name = catalog.get("time_dimension")
    date_range = validated["date_range"]
    if date_range:
        if not time_dimension_name or time_dimension_name not in catalog["dimensions"]:
            raise ValueError("Catalog does not define a valid time_dimension")
        time_column = catalog["dimensions"][time_dimension_name]["column"]
        if date_range.get("start"):
            where_clauses.append(f"{time_column} >= %s")
            params.append(date_range["start"])
        if date_range.get("end"):
            where_clauses.append(f"{time_column} <= %s")
            params.append(date_range["end"])

    for item in validated["filters"]:
        column = catalog["dimensions"][item["dimension"]]["column"]
        operator = item["operator"]
        value = item["value"]

        if operator == "in":
            placeholders = ", ".join(["%s"] * len(value))
            where_clauses.append(f"{column} in ({placeholders})")
            params.extend(value)
        else:
            where_clauses.append(f"{column} {operator} %s")
            params.append(value)

    if where_clauses:
        sql_parts.append("where " + "\n  and ".join(where_clauses))

    if dimension_columns:
        sql_parts.append("group by " + ", ".join(dimension_columns))

    sql_parts.append(f"order by {metric_name} {validated['order']}")
    sql_parts.append("limit %s")
    params.append(validated["limit"])

    return "\n".join(sql_parts), params
