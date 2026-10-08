from __future__ import annotations

from typing import Any, Literal

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
        return {
            "domain": selected_domain,
            "query": semantic_query,
            "sql": sql_text,
            "params": params,
        }

    return run_semantic_query(semantic_query, catalog=catalog)
