import unittest
from unittest.mock import patch

from semantic_api.natural_language_service import run_natural_language_query


@patch("semantic_api.natural_language_service.record_query_run")
class NaturalLanguageServiceTests(unittest.TestCase):
    def test_rules_dry_run_routes_operations_domain(self, record_query_run):
        result = run_natural_language_query(
            "Which hotel generated the most revenue in September 2026?",
            domain="auto",
            parser="rules",
            execute=False,
        )

        self.assertEqual(result["domain"], "hotel_operations")
        self.assertEqual(result["query"]["metric"], "total_revenue")
        self.assertIn("analytics_dev_ops.mart_power_bi_hotel_daily", result["sql"])
        self.assertTrue(result["query_run_id"])
        record_query_run.assert_called_once()

    def test_rules_dry_run_routes_data_quality_domain(self, record_query_run):
        result = run_natural_language_query(
            "Which source system had the lowest data quality pass rate in September 2026?",
            domain="auto",
            parser="rules",
            execute=False,
        )

        self.assertEqual(result["domain"], "data_quality")
        self.assertEqual(result["query"]["metric"], "pass_rate")
        self.assertIn("analytics_dev_dq.mart_power_bi_dq_rule_daily", result["sql"])
        self.assertTrue(result["query_run_id"])
        record_query_run.assert_called_once()

    @patch("semantic_api.natural_language_service.run_semantic_query")
    def test_execute_uses_selected_domain_catalog(
        self,
        run_query,
        record_query_run,
    ):
        run_query.return_value = {
            "domain": "hotel_operations",
            "answer": "Example answer.",
            "query": {},
            "sql": "select 1",
            "rows": [],
        }

        result = run_natural_language_query(
            "Show total revenue by hotel in September 2026",
            domain="hotel_operations",
            parser="rules",
            execute=True,
        )

        self.assertEqual(result["answer"], "Example answer.")
        self.assertTrue(result["query_run_id"])
        catalog = run_query.call_args.kwargs["catalog"]
        self.assertEqual(catalog["domain"], "hotel_operations")
        self.assertEqual(catalog["access_role"], "hotel_ops_reader")


if __name__ == "__main__":
    unittest.main()
