from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
SEMANTIC_DIR = ROOT / "semantic"
DEFAULT_DOMAIN = "hotel_operations"
DEFAULT_CATALOG_PATH = SEMANTIC_DIR / "hotel_operations.yml"
DOMAIN_REGISTRY_PATH = SEMANTIC_DIR / "domains.yml"


class CatalogError(ValueError):
    """Raised when the semantic catalog is missing or invalid."""


def _load_yaml(path: str | Path) -> dict[str, Any]:
    yaml_path = Path(path)
    if not yaml_path.exists():
        raise CatalogError(f"Semantic YAML not found: {yaml_path}")

    with yaml_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)

    if not isinstance(payload, dict):
        raise CatalogError(f"Semantic YAML must be an object: {yaml_path}")

    return payload


def load_domain_registry(path: str | Path = DOMAIN_REGISTRY_PATH) -> dict[str, Any]:
    registry = _load_yaml(path)
    domains = registry.get("domains")
    if not isinstance(domains, dict) or not domains:
        raise CatalogError("Domain registry must define at least one domain")
    return registry


def available_domains(registry: dict[str, Any] | None = None) -> list[str]:
    registry = registry or load_domain_registry()
    return sorted(registry["domains"].keys())


def load_catalog(path: str | Path = DEFAULT_CATALOG_PATH) -> dict[str, Any]:
    catalog = _load_yaml(path)

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


def load_catalog_for_domain(
    domain: str,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    registry = registry or load_domain_registry()
    domain_config = registry["domains"].get(domain)
    if not isinstance(domain_config, dict):
        raise CatalogError(f"Unknown semantic domain: {domain!r}")

    catalog_name = domain_config.get("catalog")
    if not catalog_name:
        raise CatalogError(f"Domain {domain!r} does not define a catalog")

    catalog = load_catalog(SEMANTIC_DIR / catalog_name)
    if catalog.get("domain") != domain:
        raise CatalogError(
            f"Catalog domain {catalog.get('domain')!r} does not match registry domain {domain!r}"
        )
    return catalog


def resolve_source_relation(catalog: dict[str, Any]) -> str:
    source = catalog["source"]
    schema = os.getenv(
        source.get("schema_env", "TARGET_SCHEMA"),
        source.get("default_schema", "analytics_dev"),
    )
    relation = source["relation"]
    return f"{schema}.{relation}"
