import argparse
import json

from semantic_api.catalog import load_catalog
from semantic_api.nl_parser import parse_question
from semantic_api.query_service import run_semantic_query
from semantic_api.sql_generator import generate_sql


def parse_args():
    parser = argparse.ArgumentParser(
        description="Translate a stakeholder question into a governed semantic query"
    )
    parser.add_argument("--question", required=True, help="Natural-language question")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the semantic query and generated SQL without querying PostgreSQL",
    )
    parser.add_argument(
        "--show-details",
        action="store_true",
        help="Also print the semantic query, SQL, and returned rows",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    catalog = load_catalog()
    semantic_query = parse_question(args.question, catalog)

    if args.dry_run:
        sql, params = generate_sql(semantic_query, catalog)
        print("semantic_query=")
        print(json.dumps(semantic_query, indent=2))
        print("sql=")
        print(sql)
        print(f"params={params}")
        return

    result = run_semantic_query(semantic_query)
    print(result["answer"])

    if args.show_details:
        print("details=")
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
