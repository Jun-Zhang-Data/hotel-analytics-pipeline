from __future__ import annotations

import json
import os
from typing import Any

from semantic_api.validator import validate_query


class LLMParserError(ValueError):
    """Raised when the LLM parser cannot produce a safe semantic query."""


def build_llm_prompt(question: str, catalog: dict[str, Any]) -> str:
    metrics = {
        name: definition.get("description", "")
        for name, definition in catalog["metrics"].items()
    }
    dimensions = {
        name: definition.get("description", "")
        for name, definition in catalog["dimensions"].items()
    }
    policy = catalog.get("query_policy", {})
    max_limit = int(policy.get("max_limit", 100))

    return f"""You translate stakeholder analytics questions into a governed semantic query.

You must never write SQL. You may only use the governed catalog below.

Allowed metrics:
{json.dumps(metrics, indent=2)}

Allowed dimensions:
{json.dumps(dimensions, indent=2)}

Allowed filter operators: =, !=, in
Maximum limit: {max_limit}

Return JSON only, with exactly this top-level shape:
{{
  "status": "query" or "clarification",
  "message": string or null,
  "query": {{
    "metric": string,
    "dimensions": [string],
    "filters": [
      {{
        "dimension": string,
        "operator": "=" or "!=" or "in",
        "value": string or number or [string]
      }}
    ],
    "date_range": {{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}} or null,
    "order": "asc" or "desc",
    "limit": integer
  }} or null
}}

Rules:
- Use only metric and dimension names from the catalog.
- Do not invent metrics, dimensions, tables, columns, SQL, or business definitions.
- If a named month is provided without a year, return status "clarification".
- If the requested metric is not governed by the catalog, return status "clarification".
- If the question is ambiguous enough that multiple materially different queries are possible, return status "clarification".
- For "highest", "most", or "top", use order "desc".
- For "lowest", "least", or "bottom", use order "asc".
- For a single best/worst result, use limit 1.
- Keep filters empty unless the stakeholder explicitly constrains a dimension value.
- The date range must reflect only dates explicitly supported by the question.

Stakeholder question:
{question}
"""


def _decode_model_output(output_text: str) -> dict[str, Any]:
    text = output_text.strip()
    fence = chr(96) * 3
    if text.startswith(fence):
        lines = text.splitlines()
        if lines and lines[0].startswith(fence):
            lines = lines[1:]
        if lines and lines[-1].strip() == fence:
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMParserError("LLM did not return valid JSON.") from exc

    if not isinstance(payload, dict):
        raise LLMParserError("LLM response must be a JSON object.")

    return payload


def parse_question_with_llm(
    question: str,
    catalog: dict[str, Any],
    *,
    client=None,
    model: str | None = None,
) -> dict[str, Any]:
    if not isinstance(question, str) or not question.strip():
        raise LLMParserError("Question must be a non-empty string.")

    if client is None:
        if not os.getenv("OPENAI_API_KEY"):
            raise LLMParserError(
                "OPENAI_API_KEY is not set. Configure it before using the LLM parser."
            )
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMParserError(
                "The openai package is not installed. Run pip install -r requirements.txt."
            ) from exc
        client = OpenAI()

    selected_model = model or os.getenv("OPENAI_SEMANTIC_MODEL", "gpt-6-luna")
    response = client.responses.create(
        model=selected_model,
        input=build_llm_prompt(question, catalog),
    )
    payload = _decode_model_output(response.output_text)

    status = payload.get("status")
    if status == "clarification":
        message = payload.get("message") or "The question needs clarification."
        raise LLMParserError(message)

    if status != "query":
        raise LLMParserError("LLM response status must be 'query' or 'clarification'.")

    query = payload.get("query")
    if not isinstance(query, dict):
        raise LLMParserError("LLM query payload is missing or invalid.")

    return validate_query(query, catalog)
