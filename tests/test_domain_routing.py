import unittest

from semantic_api.catalog import (
    available_domains,
    load_catalog_for_domain,
    load_domain_registry,
)
from semantic_api.domain_router import DomainRoutingError, route_domain
from semantic_api.nl_parser import parse_question
from semantic_api.sql_generator import generate_sql


class DomainRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_domain_registry()

    def test_registry_contains_expected_domains(self):
        self.assertEqual(
            available_domains(self.registry),
            ["data_quality", "hotel_operations"],
        )

    def test_routes_operations_question(self):
        domain = route_domain(
            "Which hotel generated the most revenue in September 2026?",
            self.registry,
        )
        self.assertEqual(domain, "hotel_operations")

    def test_routes_data_quality_question(self):
        domain = route_domain(
            "Which source system had the lowest data quality pass rate in September 2026?",
            self.registry,
        )
        self.assertEqual(domain, "data_quality")

    def test_unknown_domain_question_requires_clarification(self):
        with self.assertRaises(DomainRoutingError):
            route_domain(
                "What was customer satisfaction last month?",
                self.registry,
            )

    def test_data_quality_catalog_generates_governed_sql(self):
        catalog = load_catalog_for_domain("data_quality", self.registry)
        query = parse_question(
            "Which source system had the lowest data quality pass rate in September 2026?",
            catalog,
        )
        sql, params = generate_sql(query, catalog)

        self.assertEqual(query["metric"], "pass_rate")
        self.assertEqual(query["dimensions"], ["source_system"])
        self.assertEqual(query["order"], "asc")
        self.assertEqual(query["limit"], 1)
        self.assertIn("from analytics_dev_dq.mart_power_bi_dq_rule_daily", sql)
        self.assertIn("group by source_system_code", sql)
        self.assertEqual(params, ["2026-09-01", "2026-09-30", 1])


if __name__ == "__main__":
    unittest.main()
