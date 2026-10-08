import argparse
import json

from semantic_api.catalog import (
    available_domains,
    load_catalog_for_domain,
    load_domain_registry,
)
from semantic_api.domain_router import route_domain, route_domain_with_llm
from semantic_api.llm_parser import parse_question_with_llm
from semantic_api.nl_parser import parse_question
from semantic_api.query_service import run_semantic_query
from semantic_api.sql_generator import generate_sql


def parse_args():
    registry = load_domain_registry()
    parser = argparse.ArgumentParser(
        description="Translate a stakeholder question into a governed semantic query"
    )
    parser.add_argument("--question", required=True, help="Natural-language question")
    parser.add_argument(
        "--parser",
        choices=["rules", "llm"],
        default="rules",
        help="Use deterministic rules or an LLM to map language into the semantic contract",
    )
    parser.add_argument(
        "--domain",
        choices=["auto", *available_domains(registry)],
        default="auto",
        help="Use a specific governed domain or route the question automatically",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the selected domain, semantic query and SQL without querying PostgreSQL",
    )
    parser.add_argument(
        "--show-details",
        action="store_true",
        help="Also print the selected domain, semantic query, SQL and returned rows",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    registry = load_domain_registry()

    if args.domain == "auto":
        if args.parser == "llm":
            domain = route_domain_with_llm(args.question, registry)
        else:
            domain = route_domain(args.question, registry)
    else:
        domain = args.domain

    catalog = load_catalog_for_domain(domain, registry)

    if args.parser == "llm":
        semantic_query = parse_question_with_llm(args.question, catalog)
    else:
        semantic_query = parse_question(args.question, catalog)

    if args.dry_run:
        sql, params = generate_sql(semantic_query, catalog)
        print(f"domain={domain}")
        print("semantic_query=")
        print(json.dumps(semantic_query, indent=2))
        print("sql=")
        print(sql)
        print(f"params={params}")
        return

    result = run_semantic_query(semantic_query, catalog=catalog)
    print(result["answer"])

    if args.show_details:
        print("details=")
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
