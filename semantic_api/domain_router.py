from __future__ import annotations

import json
import os
import re
from typing import Any

from semantic_api.catalog import available_domains


class DomainRoutingError(ValueError):
    """Raised when a question cannot be mapped to one governed domain."""


def _contains_alias(question: str, alias: str) -> bool:
    pattern = r"\b" + re.escape(alias.lower()) + r"\b"
    return re.search(pattern, question) is not None


def route_domain(question: str, registry: dict[str, Any]) -> str:
    if not isinstance(question, str) or not question.strip():
        raise DomainRoutingError("Question must be a non-empty string.")

    normalized = " ".join(question.lower().split())
    scores: dict[str, int] = {}

    for domain, config in registry["domains"].items():
        score = 0
        for alias in config.get("aliases", []):
            if _contains_alias(normalized, alias):
                score += max(1, len(alias.split()))
        scores[domain] = score

    best_score = max(scores.values(), default=0)
    winners = [domain for domain, score in scores.items() if score == best_score]

    if best_score == 0:
        raise DomainRoutingError(
            "I could not identify which governed domain this question belongs to."
        )
    if len(winners) != 1:
        raise DomainRoutingError(
            "The question matches multiple governed domains. Please choose a domain."
        )

    return winners[0]


def build_domain_prompt(question: str, registry: dict[str, Any]) -> str:
    domains = {
        name: config.get("description", "")
        for name, config in registry["domains"].items()
    }
    return f"""Classify the stakeholder question into exactly one governed analytics domain.

Allowed domains:
{json.dumps(domains, indent=2)}

Return JSON only:
{{
  "status": "domain" or "clarification",
  "domain": one allowed domain name or null,
  "message": string or null
}}

Rules:
- Choose only from the allowed domains.
- If the question could materially belong to multiple domains, request clarification.
- If none of the domains fits, request clarification.
- Do not write SQL and do not answer the analytics question.

Stakeholder question:
{question}
"""


def route_domain_with_llm(
    question: str,
    registry: dict[str, Any],
    *,
    client=None,
    model: str | None = None,
) -> str:
    if client is None:
        if not os.getenv("OPENAI_API_KEY"):
            raise DomainRoutingError(
                "OPENAI_API_KEY is not set. Configure it before using LLM routing."
            )
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise DomainRoutingError(
                "The openai package is not installed."
            ) from exc
        client = OpenAI()

    selected_model = model or os.getenv("OPENAI_SEMANTIC_MODEL")
    if not selected_model:
        raise DomainRoutingError(
            "OPENAI_SEMANTIC_MODEL is not set. Configure the model explicitly."
        )

    response = client.responses.create(
        model=selected_model,
        input=build_domain_prompt(question, registry),
    )

    try:
        payload = json.loads(response.output_text.strip())
    except json.JSONDecodeError as exc:
        raise DomainRoutingError("Domain router did not return valid JSON.") from exc

    if payload.get("status") == "clarification":
        raise DomainRoutingError(
            payload.get("message") or "The domain needs clarification."
        )

    domain = payload.get("domain")
    if domain not in available_domains(registry):
        raise DomainRoutingError(f"Router returned unknown domain: {domain!r}")

    return domain
