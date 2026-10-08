import os
import unittest
from unittest.mock import MagicMock, patch

from semantic_api.query_service import (
    DEFAULT_STATEMENT_TIMEOUT_MS,
    _configure_query_session,
    _statement_timeout_ms,
)


class QueryServiceSafetyTests(unittest.TestCase):
    def test_default_statement_timeout(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                _statement_timeout_ms(),
                DEFAULT_STATEMENT_TIMEOUT_MS,
            )

    def test_statement_timeout_can_be_overridden(self):
        with patch.dict(
            os.environ,
            {"SEMANTIC_STATEMENT_TIMEOUT_MS": "2500"},
            clear=True,
        ):
            self.assertEqual(_statement_timeout_ms(), 2500)

    def test_invalid_statement_timeout_is_rejected(self):
        with patch.dict(
            os.environ,
            {"SEMANTIC_STATEMENT_TIMEOUT_MS": "0"},
            clear=True,
        ):
            with self.assertRaises(ValueError):
                _statement_timeout_ms()

    def test_query_session_is_read_only_and_timed(self):
        connection = MagicMock()
        cursor = MagicMock()

        with patch.dict(
            os.environ,
            {"SEMANTIC_STATEMENT_TIMEOUT_MS": "3000"},
            clear=True,
        ):
            _configure_query_session(connection, cursor)

        connection.set_session.assert_called_once_with(readonly=True)
        cursor.execute.assert_called_once_with(
            "select set_config('statement_timeout', %s, true)",
            ("3000",),
        )


if __name__ == "__main__":
    unittest.main()
