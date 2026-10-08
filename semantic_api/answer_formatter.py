from __future__ import annotations

from decimal import Decimal
from typing import Any


def _label(name: str) -> str:
    return name.replace("_", " ").title()


def _format_value(
    metric: str,
    value: Any,
    catalog: dict[str, Any],
) -> str:
    if value is None:
        return "N/A"

    metric_format = catalog["metrics"].get(metric, {}).get("format", "number")
    if metric_format == "percent":
        return f"{float(value) * 100:.2f}%"

    if isinstance(value, (int, float, Decimal)):
        numeric = float(value)
        if numeric.is_integer():
            return f"{int(numeric):,}"
        return f"{numeric:,.2f}"

    return str(value)


def _date_context(query: dict[str, Any]) -> str:
    date_range = query.get("date_range")
    if not date_range:
        return ""

    start = date_range.get("start")
    end = date_range.get("end")
    if start and end:
        if start == end:
            return f"On {start}, "
        return f"From {start} to {end}, "
    if start:
        return f"From {start}, "
    if end:
        return f"Through {end}, "
    return ""


def format_answer(
    query: dict[str, Any],
    rows: list[dict[str, Any]],
    catalog: dict[str, Any],
) -> str:
    if not rows:
        return "No matching data was found for the requested query."

    metric = query["metric"]
    metric_label = _label(metric)
    dimensions = query.get("dimensions", [])
    date_context = _date_context(query)

    if not dimensions:
        value = _format_value(metric, rows[0].get(metric), catalog)
        return f"{date_context}{metric_label} was {value}."

    if len(dimensions) == 1:
        dimension = dimensions[0]
        dimension_column = catalog["dimensions"][dimension]["column"]

        if len(rows) == 1:
            entity = rows[0].get(dimension_column, "Unknown")
            value = _format_value(metric, rows[0].get(metric), catalog)
            return f"{date_context}{entity}: {metric_label} was {value}."

        parts = []
        for row in rows:
            entity = row.get(dimension_column, "Unknown")
            value = _format_value(metric, row.get(metric), catalog)
            parts.append(f"{entity} = {value}")
        return f"{date_context}{metric_label}: " + "; ".join(parts) + "."

    formatted_rows = []
    for row in rows:
        dimension_values = []
        for dimension in dimensions:
            column = catalog["dimensions"][dimension]["column"]
            dimension_values.append(str(row.get(column, "Unknown")))
        value = _format_value(metric, row.get(metric), catalog)
        formatted_rows.append(f"{' / '.join(dimension_values)} = {value}")

    return f"{date_context}{metric_label}: " + "; ".join(formatted_rows) + "."
