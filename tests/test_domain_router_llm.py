import json
import unittest

from semantic_api.catalog import load_domain_registry
from semantic_api.domain_router import DomainRoutingError, route_domain_with_llm


class _FakeResponse:
    def __init__(self, output_text):
        self.output_text = output_text


class _FakeResponses:
    def __init__(self, output_text):
        self.output_text = output_text

    def create(self, **kwargs):
        return _FakeResponse(self.output_text)


class _FakeClient:
    def __init__(self, output_text):
        self.responses = _FakeResponses(output_text)


class LLMDomainRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_domain_registry()

    def test_llm_routes_known_domain(self):
        client = _FakeClient(
            json.dumps(
                {
                    "status": "domain",
                    "domain": "data_quality",
                    "message": None,
                }
            )
        )
        domain = route_domain_with_llm(
            "Which source system has the lowest pass rate?",
            self.registry,
            client=client,
            model="test-model",
        )
        self.assertEqual(domain, "data_quality")

    def test_llm_clarification_is_respected(self):
        client = _FakeClient(
            json.dumps(
                {
                    "status": "clarification",
                    "domain": None,
                    "message": "Please specify whether you mean operations or data quality.",
                }
            )
        )
        with self.assertRaisesRegex(DomainRoutingError, "Please specify"):
            route_domain_with_llm(
                "Show me the worst source.",
                self.registry,
                client=client,
                model="test-model",
            )

    def test_llm_unknown_domain_is_rejected(self):
        client = _FakeClient(
            json.dumps(
                {
                    "status": "domain",
                    "domain": "finance",
                    "message": None,
                }
            )
        )
        with self.assertRaises(DomainRoutingError):
            route_domain_with_llm(
                "Show finance metrics.",
                self.registry,
                client=client,
                model="test-model",
            )


if __name__ == "__main__":
    unittest.main()
