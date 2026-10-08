import json
import unittest

from semantic_api.catalog import load_catalog
from semantic_api.llm_parser import (
    LLMParserError,
    _decode_model_output,
    build_llm_prompt,
    parse_question_with_llm,
)


class _FakeResponse:
    def __init__(self, output_text):
        self.output_text = output_text


class _FakeResponses:
    def __init__(self, output_text):
        self.output_text = output_text
        self.last_call = None

    def create(self, **kwargs):
        self.last_call = kwargs
        return _FakeResponse(self.output_text)


class _FakeClient:
    def __init__(self, output_text):
        self.responses = _FakeResponses(output_text)


class LLMParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog()

    def test_prompt_contains_governed_catalog_and_no_sql_instruction(self):
        prompt = build_llm_prompt(
            "Which hotel had the most revenue in September 2026?",
            self.catalog,
        )
        self.assertIn("total_revenue", prompt)
        self.assertIn("hotel", prompt)
        self.assertIn("must never write SQL", prompt)

    def test_decodes_fenced_json(self):
        fence = chr(96) * 3
        text = (
            fence
            + 'json\n{"status":"clarification","message":"Need a year","query":null}\n'
            + fence
        )
        payload = _decode_model_output(text)
        self.assertEqual(payload["status"], "clarification")

    def test_valid_llm_query_is_still_validated(self):
        output = json.dumps(
            {
                "status": "query",
                "message": None,
                "query": {
                    "metric": "total_revenue",
                    "dimensions": ["hotel"],
                    "filters": [],
                    "date_range": {
                        "start": "2026-09-01",
                        "end": "2026-09-30",
                    },
                    "order": "desc",
                    "limit": 1,
                },
            }
        )
        client = _FakeClient(output)

        query = parse_question_with_llm(
            "Which hotel had the most revenue in September 2026?",
            self.catalog,
            client=client,
            model="test-model",
        )

        self.assertEqual(query["metric"], "total_revenue")
        self.assertEqual(query["dimensions"], ["hotel"])
        self.assertEqual(query["limit"], 1)
        self.assertEqual(client.responses.last_call["model"], "test-model")

    def test_clarification_is_not_executed(self):
        output = json.dumps(
            {
                "status": "clarification",
                "message": "Please include a year.",
                "query": None,
            }
        )

        with self.assertRaisesRegex(LLMParserError, "Please include a year"):
            parse_question_with_llm(
                "Which hotel had the most revenue in September?",
                self.catalog,
                client=_FakeClient(output),
                model="test-model",
            )

    def test_invalid_json_is_rejected(self):
        with self.assertRaises(LLMParserError):
            _decode_model_output("not-json")


if __name__ == "__main__":
    unittest.main()
