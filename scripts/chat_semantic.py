import argparse
import json

from semantic_api.catalog import load_catalog
from semantic_api.llm_parser import LLMParserError, parse_question_with_llm
from semantic_api.query_service import run_semantic_query


def parse_args():
    parser = argparse.ArgumentParser(
        description="Interactive governed analytics chat over the semantic layer"
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

    print("Hotel Analytics Chat")
    print("Ask a governed hotel-operations question. Type 'exit' to quit.")

    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue

        try:
            semantic_query = parse_question_with_llm(question, catalog)
            result = run_semantic_query(semantic_query)
            print(result["answer"])

            if args.show_details:
                print(json.dumps(result, indent=2, default=str))
        except LLMParserError as exc:
            print(f"Clarification needed: {exc}")
        except Exception as exc:
            print(f"Query failed: {exc}")


if __name__ == "__main__":
    main()
