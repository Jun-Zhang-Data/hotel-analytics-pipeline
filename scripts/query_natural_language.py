import argparse
import json

from semantic_api.catalog import available_domains, load_domain_registry
from semantic_api.natural_language_service import run_natural_language_query


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
    result = run_natural_language_query(
        args.question,
        domain=args.domain,
        parser=args.parser,
        execute=not args.dry_run,
    )

    if args.dry_run:
        print(f"domain={result['domain']}")
        print("semantic_query=")
        print(json.dumps(result["query"], indent=2))
        print("sql=")
        print(result["sql"])
        print(f"params={result['params']}")
        return

    print(result["answer"])

    if args.show_details:
        print("details=")
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
