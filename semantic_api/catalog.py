from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG_PATH = ROOT / "semantic" / "hotel_operations.yml"


class CatalogError(ValueError):
    """Raised when the semantic catalog is missing or invalid."""


def load_catalog(path: str | Path = DEFAULT_CATALOG_PATH) -> dict[str, Any]:
    catalog_path = Path(path)
    if not catalog_path.exists():
        raise CatalogError(f"Semantic catalog not found: {catalog_path}")

    with catalog_path.open("r", encoding="utf-8") as handle:
        catalog = yaml.safe_load(handle)

    if not isinstance(catalog, dict):
        raise CatalogError("Semantic catalog must be a YAML object")

    for required_key in ("domain", "source", "dimensions", "metrics"):
        if required_key not in catalog:
            raise CatalogError(f"Semantic catalog missing required key: {required_key}")

    source = catalog["source"]
    if not isinstance(source, dict) or "relation" not in source:
        raise CatalogError("Semantic catalog source must define relation")

    if not isinstance(catalog["dimensions"], dict) or not catalog["dimensions"]:
        raise CatalogError("Semantic catalog must define at least one dimension")

    if not isinstance(catalog["metrics"], dict) or not catalog["metrics"]:
        raise CatalogError("Semantic catalog must define at least one metric")

    return catalog


def resolve_source_relation(catalog: dict[str, Any]) -> str:
    source = catalog["source"]
    schema = os.getenv(
        source.get("schema_env", "TARGET_SCHEMA"),
        source.get("default_schema", "analytics_dev"),
    )
    relation = source["relation"]
    return f"{schema}.{relation}"
