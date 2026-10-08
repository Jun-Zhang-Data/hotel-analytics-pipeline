from __future__ import annotations

from time import perf_counter
from typing import Any, Literal
from uuid import uuid4

from semantic_api.audit import record_query_run
from semantic_api.catalog import (
    available_domains,
    load_catalog_for_domain,
    load_domain_registry,
)
from semantic_api.domain_router import (
    DomainRoutingError,
    route_domain,
    route_domain_with_llm,
)
from semantic_api.llm_parser import parse_question_with_llm
from semantic_api.nl_parser import parse_question
from semantic_api.query_service import run_semantic_query
from semantic_api.sql_generator import generate_sql


ParserMode = Literal["rules", "llm"]


def resolve_domain(
    question: str,
    *,
    domain: str = "auto",
    parser: ParserMode = "llm",
    registry: dict[str, Any] | None = None,
) -> str:
    registry = registry or load_domain_registry()

    if domain != "auto":
        if domain not in available_domains(registry):
            raise DomainRoutingError(f"Unknown semantic domain: {domain!r}")
        return domain

    if parser == "llm":
        return route_domain_with_llm(question, registry)

    return route_domain(question, registry)


def build_semantic_query(
    question: str,
    catalog: dict[str, Any],
    *,
    parser: ParserMode = "llm",
) -> dict[str, Any]:
    if parser == "llm":
        return parse_question_with_llm(question, catalog)
    return parse_question(question, catalog)


def run_natural_language_query(
    question: str,
    *,
    domain: str = "auto",
    parser: ParserMode = "llm",
    execute: bool = True,
) -> dict[str, Any]:
    query_run_id = str(uuid4())
    started = perf_counter()
    selected_domain: str | None = None
    catalog: dict[str, Any] | None = None
    semantic_query: dict[str, Any] | None = None
    execution_mode = "EXECUTE" if execute else "DRY_RUN"

    try:
        registry = load_domain_registry()
        selected_domain = resolve_domain(
            question,
            domain=domain,
            parser=parser,
            registry=registry,
        )
        catalog = load_catalog_for_domain(selected_domain, registry)
        semantic_query = build_semantic_query(
            question,
            catalog,
            parser=parser,
        )

        if not execute:
            sql_text, params = generate_sql(semantic_query, catalog)
            result = {
                "query_run_id": query_run_id,
                "domain": selected_domain,
                "query": semantic_query,
                "sql": sql_text,
                "params": params,
            }
        else:
            result = run_semantic_query(semantic_query, catalog=catalog)
            result["query_run_id"] = query_run_id

        duration_ms = int((perf_counter() - started) * 1000)
        record_query_run(
            query_run_id=query_run_id,
            question=question,
            parser=parser,
            requested_domain=domain,
            selected_domain=selected_domain,
            metric=semantic_query.get("metric"),
            access_role=catalog.get("access_role"),
            execution_mode=execution_mode,
            status="SUCCESS",
            row_count=len(result.get("rows", [])) if execute else None,
            duration_ms=duration_ms,
        )
        return result
    except Exception as exc:
        duration_ms = int((perf_counter() - started) * 1000)
        record_query_run(
            query_run_id=query_run_id,
            question=question,
            parser=parser,
            requested_domain=domain,
            selected_domain=selected_domain,
            metric=semantic_query.get("metric") if semantic_query else None,
            access_role=catalog.get("access_role") if catalog else None,
            execution_mode=execution_mode,
            status="FAILED",
            row_count=None,
            duration_ms=duration_ms,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        raise
