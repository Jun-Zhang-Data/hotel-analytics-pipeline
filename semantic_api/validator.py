from __future__ import annotations

from datetime import date
from typing import Any


class SemanticQueryError(ValueError):
    """Raised when a semantic query asks for unsupported or unsafe fields."""


ALLOWED_FILTER_OPERATORS = {"=", "!=", "in"}
ALLOWED_ORDER_DIRECTIONS = {"asc", "desc"}


def _validate_iso_date(value: str, label: str) -> None:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise SemanticQueryError(f"{label} must be an ISO date (YYYY-MM-DD)") from exc


def validate_query(query: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(query, dict):
        raise SemanticQueryError("Semantic query must be a JSON object")

    metric = query.get("metric")
    if metric not in catalog["metrics"]:
        raise SemanticQueryError(f"Unknown metric: {metric!r}")

    dimensions = query.get("dimensions", [])
    if not isinstance(dimensions, list):
        raise SemanticQueryError("dimensions must be a list")
    for dimension in dimensions:
        if dimension not in catalog["dimensions"]:
            raise SemanticQueryError(f"Unknown dimension: {dimension!r}")

    filters = query.get("filters", [])
    if not isinstance(filters, list):
        raise SemanticQueryError("filters must be a list")

    normalized_filters: list[dict[str, Any]] = []
    for item in filters:
        if not isinstance(item, dict):
            raise SemanticQueryError("Each filter must be an object")
        dimension = item.get("dimension")
        operator = str(item.get("operator", "=")).lower()
        value = item.get("value")

        if dimension not in catalog["dimensions"]:
            raise SemanticQueryError(f"Unknown filter dimension: {dimension!r}")
        if operator not in ALLOWED_FILTER_OPERATORS:
            raise SemanticQueryError(f"Unsupported filter operator: {operator!r}")
        if operator == "in" and (not isinstance(value, list) or not value):
            raise SemanticQueryError("IN filters require a non-empty list value")

        normalized_filters.append(
            {"dimension": dimension, "operator": operator, "value": value}
        )

    date_range = query.get("date_range")
    if date_range is not None:
        if not isinstance(date_range, dict):
            raise SemanticQueryError("date_range must be an object")
        start = date_range.get("start")
        end = date_range.get("end")
        if start:
            _validate_iso_date(start, "date_range.start")
        if end:
            _validate_iso_date(end, "date_range.end")
        if start and end and start > end:
            raise SemanticQueryError("date_range.start must be on or before date_range.end")

    order = str(query.get("order", "desc")).lower()
    if order not in ALLOWED_ORDER_DIRECTIONS:
        raise SemanticQueryError("order must be 'asc' or 'desc'")

    policy = catalog.get("query_policy", {})
    default_limit = int(policy.get("default_limit", 20))
    max_limit = int(policy.get("max_limit", 100))
    limit = int(query.get("limit", default_limit))
    if limit < 1 or limit > max_limit:
        raise SemanticQueryError(f"limit must be between 1 and {max_limit}")

    return {
        "metric": metric,
        "dimensions": dimensions,
        "filters": normalized_filters,
        "date_range": date_range,
        "order": order,
        "limit": limit,
    }
