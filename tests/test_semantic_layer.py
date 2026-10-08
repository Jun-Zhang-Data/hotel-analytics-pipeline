import os
import unittest

from semantic_api.catalog import load_catalog, resolve_source_relation
from semantic_api.sql_generator import generate_sql
from semantic_api.validator import SemanticQueryError, validate_query


class SemanticLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog()

    def test_catalog_resolves_default_source(self):
        old_value = os.environ.pop("TARGET_SCHEMA", None)
        try:
            self.assertEqual(
                resolve_source_relation(self.catalog),
                "analytics_dev.mart_power_bi_hotel_daily",
            )
        finally:
            if old_value is not None:
                os.environ["TARGET_SCHEMA"] = old_value

    def test_valid_query_is_normalized(self):
        query = {
            "metric": "total_revenue",
            "dimensions": ["hotel"],
            "date_range": {"start": "2026-09-01", "end": "2026-09-30"},
            "order": "desc",
            "limit": 5,
        }
        validated = validate_query(query, self.catalog)
        self.assertEqual(validated["metric"], "total_revenue")
        self.assertEqual(validated["dimensions"], ["hotel"])
        self.assertEqual(validated["limit"], 5)

    def test_unknown_metric_is_rejected(self):
        with self.assertRaises(SemanticQueryError):
            validate_query({"metric": "made_up_metric"}, self.catalog)

    def test_sql_is_generated_from_catalog_and_uses_parameters(self):
        query = {
            "metric": "total_revenue",
            "dimensions": ["city"],
            "filters": [
                {"dimension": "city", "operator": "=", "value": "Stockholm"}
            ],
            "date_range": {"start": "2026-09-01", "end": "2026-09-30"},
            "limit": 3,
        }
        sql, params = generate_sql(query, self.catalog)

        self.assertIn("from analytics_dev.mart_power_bi_hotel_daily", sql)
        self.assertIn("sum(total_revenue) as total_revenue", sql)
        self.assertIn("group by city", sql)
        self.assertIn("city = %s", sql)
        self.assertNotIn("Stockholm", sql)
        self.assertEqual(params, ["2026-09-01", "2026-09-30", "Stockholm", 3])

    def test_limit_policy_is_enforced(self):
        with self.assertRaises(SemanticQueryError):
            validate_query(
                {"metric": "total_bookings", "limit": 101},
                self.catalog,
            )


if __name__ == "__main__":
    unittest.main()
