import unittest
from unittest.mock import patch

from fastapi import HTTPException

from semantic_api.app import QueryRequest, domains, health, home, query_endpoint
from semantic_api.domain_router import DomainRoutingError


class SemanticApiTests(unittest.TestCase):
    def test_home_serves_browser_ui(self):
        response = home()
        body = response.body.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Hotel Analytics Chat", body)
        self.assertIn('fetch("/query"', body)

    def test_health(self):
        self.assertEqual(health(), {"status": "ok"})

    def test_domains_exposes_governed_metadata(self):
        payload = domains()
        names = [item["domain"] for item in payload["domains"]]

        self.assertEqual(names, ["data_quality", "hotel_operations"])
        for item in payload["domains"]:
            self.assertTrue(item["metrics"])
            self.assertTrue(item["dimensions"])

    @patch("semantic_api.app.run_natural_language_query")
    def test_query_hides_internal_details_by_default(self, run_query):
        run_query.return_value = {
            "domain": "hotel_operations",
            "answer": "Stockholm Central: Total Revenue was 1,250.",
            "access_role": "hotel_ops_reader",
            "query": {"metric": "total_revenue"},
            "sql": "select secret_internal_sql",
            "rows": [{"hotel_name": "Stockholm Central"}],
        }

        response = query_endpoint(
            QueryRequest(
                question="Which hotel had the most revenue?",
                domain="hotel_operations",
                parser="rules",
            )
        )

        self.assertEqual(response["domain"], "hotel_operations")
        self.assertIn("answer", response)
        self.assertNotIn("sql", response)
        self.assertNotIn("rows", response)

    @patch("semantic_api.app.run_natural_language_query")
    def test_query_can_return_details_explicitly(self, run_query):
        run_query.return_value = {
            "domain": "data_quality",
            "answer": "PMS_A: Pass Rate was 95.00%.",
            "access_role": "data_quality_reader",
            "query": {"metric": "pass_rate"},
            "sql": "select governed_sql",
            "rows": [{"source_system_code": "PMS_A"}],
        }

        response = query_endpoint(
            QueryRequest(
                question="Show pass rate.",
                domain="data_quality",
                parser="rules",
                include_details=True,
            )
        )

        self.assertEqual(response["access_role"], "data_quality_reader")
        self.assertEqual(response["sql"], "select governed_sql")
        self.assertEqual(response["semantic_query"]["metric"], "pass_rate")

    @patch("semantic_api.app.run_natural_language_query")
    def test_governance_error_returns_http_400(self, run_query):
        run_query.side_effect = DomainRoutingError("Unknown semantic domain.")

        with self.assertRaises(HTTPException) as raised:
            query_endpoint(
                QueryRequest(
                    question="Show something.",
                    domain="auto",
                    parser="rules",
                )
            )

        self.assertEqual(raised.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
