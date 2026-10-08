import unittest

from semantic_api.catalog import load_catalog
from semantic_api.nl_parser import NaturalLanguageQueryError, parse_question
from semantic_api.sql_generator import generate_sql


class NaturalLanguageParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog()

    def test_revenue_by_hotel_for_month(self):
        query = parse_question(
            "Which hotel generated the most revenue in September 2026?",
            self.catalog,
        )
        self.assertEqual(query["metric"], "total_revenue")
        self.assertEqual(query["dimensions"], ["hotel"])
        self.assertEqual(
            query["date_range"],
            {"start": "2026-09-01", "end": "2026-09-30"},
        )
        self.assertEqual(query["order"], "desc")
        self.assertEqual(query["limit"], 1)

    def test_lowest_cancellation_rate_by_city(self):
        query = parse_question(
            "Which city had the lowest cancellation rate in September 2026?",
            self.catalog,
        )
        self.assertEqual(query["metric"], "cancellation_rate")
        self.assertEqual(query["dimensions"], ["city"])
        self.assertEqual(query["order"], "asc")
        self.assertEqual(query["limit"], 1)

    def test_top_three_hotels(self):
        query = parse_question(
            "Show the top 3 hotels by total bookings in September 2026",
            self.catalog,
        )
        self.assertEqual(query["metric"], "total_bookings")
        self.assertEqual(query["dimensions"], ["hotel"])
        self.assertEqual(query["limit"], 3)

    def test_month_without_year_is_rejected(self):
        with self.assertRaises(NaturalLanguageQueryError):
            parse_question(
                "Which hotel had the most revenue in September?",
                self.catalog,
            )

    def test_unknown_metric_is_rejected(self):
        with self.assertRaises(NaturalLanguageQueryError):
            parse_question(
                "Which hotel had the best customer satisfaction score?",
                self.catalog,
            )

    def test_parsed_question_flows_to_sql_generator(self):
        query = parse_question(
            "Which city had the highest revenue in September 2026?",
            self.catalog,
        )
        sql, params = generate_sql(query, self.catalog)
        self.assertIn("sum(total_revenue) as total_revenue", sql)
        self.assertIn("group by city", sql)
        self.assertEqual(params, ["2026-09-01", "2026-09-30", 1])


if __name__ == "__main__":
    unittest.main()
