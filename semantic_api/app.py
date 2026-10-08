from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from semantic_api.catalog import (
    available_domains,
    load_catalog_for_domain,
    load_domain_registry,
)
from semantic_api.domain_router import DomainRoutingError
from semantic_api.llm_parser import LLMParserError
from semantic_api.natural_language_service import run_natural_language_query
from semantic_api.nl_parser import NaturalLanguageQueryError
from semantic_api.validator import SemanticQueryError


app = FastAPI(
    title="Hotel Analytics Semantic API",
    version="1.0.0",
    description=(
        "Governed natural-language analytics over domain-specific semantic catalogs."
    ),
)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    domain: str = "auto"
    parser: Literal["rules", "llm"] = "llm"
    include_details: bool = False


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/domains")
def domains() -> dict[str, list[dict[str, object]]]:
    registry = load_domain_registry()
    payload = []

    for domain in available_domains(registry):
        catalog = load_catalog_for_domain(domain, registry)
        payload.append(
            {
                "domain": domain,
                "description": catalog.get("description", ""),
                "metrics": sorted(catalog["metrics"].keys()),
                "dimensions": sorted(catalog["dimensions"].keys()),
            }
        )

    return {"domains": payload}


@app.post("/query")
def query_endpoint(request: QueryRequest) -> dict[str, object]:
    try:
        result = run_natural_language_query(
            request.question,
            domain=request.domain,
            parser=request.parser,
            execute=True,
        )
    except (
        DomainRoutingError,
        LLMParserError,
        NaturalLanguageQueryError,
        SemanticQueryError,
        ValueError,
    ) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response: dict[str, object] = {
        "domain": result["domain"],
        "answer": result["answer"],
    }

    if request.include_details:
        response["access_role"] = result.get("access_role")
        response["semantic_query"] = result["query"]
        response["sql"] = result["sql"]
        response["rows"] = result["rows"]

    return response
