from __future__ import annotations

import calendar
import re
from datetime import date
from typing import Any


class NaturalLanguageQueryError(ValueError):
    """Raised when a stakeholder question cannot be mapped safely."""


MONTH_LOOKUP = {
    month.lower(): index
    for index, month in enumerate(calendar.month_name)
    if month
}


def _contains_alias(question: str, alias: str) -> bool:
    pattern = r"\b" + re.escape(alias.lower()) + r"\b"
    return re.search(pattern, question) is not None


def _resolve_metric(question: str, catalog: dict[str, Any]) -> str:
    aliases = catalog.get("natural_language", {}).get("metric_aliases", {})
    matches: list[tuple[int, str]] = []

    for metric, metric_aliases in aliases.items():
        if metric not in catalog["metrics"]:
            continue
        for alias in metric_aliases:
            if _contains_alias(question, alias):
                matches.append((len(alias), metric))

    if not matches:
        raise NaturalLanguageQueryError(
            "I could not identify a governed metric in the question."
        )

    matches.sort(reverse=True)
    return matches[0][1]


def _resolve_dimensions(question: str, catalog: dict[str, Any]) -> list[str]:
    aliases = catalog.get("natural_language", {}).get("dimension_aliases", {})
    matched: list[str] = []

    for dimension, dimension_aliases in aliases.items():
        if dimension not in catalog["dimensions"] or dimension == catalog.get(
            "time_dimension"
        ):
            continue
        if any(_contains_alias(question, alias) for alias in dimension_aliases):
            matched.append(dimension)

    return matched


def _resolve_order(question: str) -> str:
    ascending_words = ("lowest", "least", "smallest", "bottom")
    if any(word in question for word in ascending_words):
        return "asc"
    return "desc"


def _resolve_limit(question: str, default_limit: int) -> int:
    top_match = re.search(r"\b(?:top|bottom|first)\s+(\d+)\b", question)
    if top_match:
        return int(top_match.group(1))

    singular_rank_words = (
        "which hotel",
        "which city",
        "highest",
        "lowest",
        "most revenue",
        "least revenue",
    )
    if any(phrase in question for phrase in singular_rank_words):
        return 1

    return default_limit


def _month_range(year: int, month: int) -> dict[str, str]:
    last_day = calendar.monthrange(year, month)[1]
    return {
        "start": date(year, month, 1).isoformat(),
        "end": date(year, month, last_day).isoformat(),
    }


def _resolve_date_range(question: str) -> dict[str, str] | None:
    iso_range = re.search(
        r"\b(\d{4}-\d{2}-\d{2})\b.*?\b(\d{4}-\d{2}-\d{2})\b",
        question,
    )
    if iso_range:
        start, end = iso_range.groups()
        return {"start": start, "end": end}

    single_iso = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", question)
    if single_iso:
        value = single_iso.group(1)
        return {"start": value, "end": value}

    month_pattern = "|".join(MONTH_LOOKUP)
    month_match = re.search(
        rf"\b({month_pattern})\s+(\d{{4}})\b",
        question,
        flags=re.IGNORECASE,
    )
    if month_match:
        month_name, year_text = month_match.groups()
        return _month_range(int(year_text), MONTH_LOOKUP[month_name.lower()])

    bare_month = re.search(
        rf"\b({month_pattern})\b",
        question,
        flags=re.IGNORECASE,
    )
    if bare_month:
        raise NaturalLanguageQueryError(
            f"Please include a year with {bare_month.group(1).title()} "
            "(for example, September 2026)."
        )

    return None


def parse_question(question: str, catalog: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(question, str) or not question.strip():
        raise NaturalLanguageQueryError("Question must be a non-empty string.")

    normalized = " ".join(question.lower().split())
    policy = catalog.get("query_policy", {})
    default_limit = int(policy.get("default_limit", 20))

    semantic_query = {
        "metric": _resolve_metric(normalized, catalog),
        "dimensions": _resolve_dimensions(normalized, catalog),
        "filters": [],
        "date_range": _resolve_date_range(normalized),
        "order": _resolve_order(normalized),
        "limit": _resolve_limit(normalized, default_limit),
    }
    return semantic_query
