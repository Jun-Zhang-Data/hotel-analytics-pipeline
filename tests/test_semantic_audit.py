import unittest

from semantic_api.audit import question_fingerprint


class SemanticAuditTests(unittest.TestCase):
    def test_question_fingerprint_is_deterministic_and_normalized(self):
        first = question_fingerprint("  Which HOTEL had most revenue?  ")
        second = question_fingerprint("which hotel had most revenue?")

        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_question_fingerprint_does_not_store_raw_question(self):
        question = "Which hotel had most revenue?"
        fingerprint = question_fingerprint(question)

        self.assertNotIn("hotel", fingerprint)
        self.assertNotEqual(question, fingerprint)


if __name__ == "__main__":
    unittest.main()
