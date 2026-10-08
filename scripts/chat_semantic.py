import argparse
import json

from semantic_api.domain_router import DomainRoutingError
from semantic_api.llm_parser import LLMParserError
from semantic_api.natural_language_service import run_natural_language_query


def parse_args():
    parser = argparse.ArgumentParser(
        description="Interactive governed analytics chat over multiple semantic domains"
    )
    parser.add_argument(
        "--show-details",
        action="store_true",
        help="Also print the selected domain, semantic query, SQL and returned rows",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("Hotel Analytics Chat")
    print("Available domains: hotel_operations, data_quality")
    print("Type 'exit' to quit.")

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
            result = run_natural_language_query(
                question,
                domain="auto",
                parser="llm",
                execute=True,
            )
            print(result["answer"])

            if args.show_details:
                print(json.dumps(result, indent=2, default=str))
        except (DomainRoutingError, LLMParserError, ValueError) as exc:
            print(f"Clarification needed: {exc}")
        except Exception as exc:
            print(f"Query failed: {exc}")


if __name__ == "__main__":
    main()
