import unittest
from decimal import Decimal

from semantic_api.answer_formatter import format_answer
from semantic_api.catalog import load_catalog


class AnswerFormatterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog()

    def test_single_hotel_revenue_answer(self):
        query = {
            "metric": "total_revenue",
            "dimensions": ["hotel"],
            "date_range": {"start": "2026-09-01", "end": "2026-09-30"},
        }
        rows = [
            {
                "hotel_name": "Stockholm Central",
                "total_revenue": Decimal("1250.50"),
            }
        ]

        answer = format_answer(query, rows, self.catalog)

        self.assertEqual(
            answer,
            "From 2026-09-01 to 2026-09-30, Stockholm Central: "
            "Total Revenue was 1,250.50.",
        )

    def test_percentage_is_formatted_for_stakeholder(self):
        query = {
            "metric": "cancellation_rate",
            "dimensions": ["city"],
            "date_range": None,
        }
        rows = [{"city": "Stockholm", "cancellation_rate": Decimal("0.125")}]

        answer = format_answer(query, rows, self.catalog)

        self.assertEqual(answer, "Stockholm: Cancellation Rate was 12.50%.")

    def test_empty_result_has_clear_message(self):
        query = {
            "metric": "total_bookings",
            "dimensions": ["hotel"],
            "date_range": None,
        }

        answer = format_answer(query, [], self.catalog)

        self.assertEqual(
            answer,
            "No matching data was found for the requested query.",
        )


if __name__ == "__main__":
    unittest.main()
