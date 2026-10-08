import argparse
import json
from pathlib import Path

from semantic_api.catalog import load_catalog
from semantic_api.query_service import run_semantic_query
from semantic_api.sql_generator import generate_sql


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a governed semantic query against hotel analytics marts"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--query-json", help="Semantic query as a JSON string")
    source.add_argument("--query-file", type=Path, help="Path to a semantic query JSON file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print generated SQL without connecting to PostgreSQL",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.query_json:
        query = json.loads(args.query_json)
    else:
        query = json.loads(args.query_file.read_text(encoding="utf-8"))

    if args.dry_run:
        catalog = load_catalog()
        sql, params = generate_sql(query, catalog)
        print(sql)
        print(f"params={params}")
        return

    result = run_semantic_query(query)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
