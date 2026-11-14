"""Tests for search spelling correction.

Run with:  python3 -m unittest test_search_spelling
"""
import os
import tempfile
import unittest

import search_engine as se

VOCAB = {
    "eligibility": 900, "overpayment": 300, "calworks": 800, "recertification": 120,
    "student": 200, "students": 150, "exemption": 90, "immediate": 80, "need": 400,
    "homeless": 70, "assistance": 600, "expedited": 60, "services": 500, "filing": 40,
    "medical": 300, "eligible": 500,
}


class EditDistanceTest(unittest.TestCase):
    def test_swap_counts_as_one_edit(self):
        self.assertEqual(se._edit_distance("calwroks", "calworks", 2), 1)

    def test_stops_past_the_limit(self):
        self.assertEqual(se._edit_distance("abcdef", "uvwxyz", 2), 3)


class CorrectQueryTest(unittest.TestCase):
    def test_fixes_single_misspelled_word(self):
        self.assertEqual(se.correct_query("eligibilty", VOCAB), "eligibility")
        self.assertEqual(se.correct_query("calwroks", VOCAB), "calworks")
        self.assertEqual(se.correct_query("recertifcation", VOCAB), "recertification")

    def test_fixes_each_word_and_keeps_the_rest(self):
        self.assertEqual(se.correct_query("studnet exemtion", VOCAB), "student exemption")
        self.assertEqual(se.correct_query("imediate need", VOCAB), "immediate need")

    def test_keeps_capitalisation(self):
        self.assertEqual(se.correct_query("Eligibilty", VOCAB), "Eligibility")

    def test_leaves_correct_text_alone(self):
        self.assertIsNone(se.correct_query("eligibility", VOCAB))
        self.assertIsNone(se.correct_query("medical", VOCAB))

    def test_leaves_codes_abbreviations_short_words_and_quotes_alone(self):
        self.assertIsNone(se.correct_query("63-103 filing", VOCAB))
        self.assertIsNone(se.correct_query("MC 180", VOCAB))
        self.assertIsNone(se.correct_query("SUA", VOCAB))
        self.assertIsNone(se.correct_query("calfrsh", VOCAB))  # handled by TOKEN_ALIASES
        self.assertIsNone(se.correct_query('"eligibilty"', VOCAB))

    def test_no_close_word_means_no_change(self):
        self.assertIsNone(se.correct_query("zzzzqqq", VOCAB))


@unittest.skipUnless(se.FTS5_AVAILABLE, "SQLite FTS5 not available")
class EngineCorrectionTest(unittest.TestCase):
    """Builds a real index from the catalog in a temporary file."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.engine = se.SearchEngine(db_path=os.path.join(cls.tmp.name, "search.db"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_misspelled_search_finds_the_document(self):
        found = self.engine.search_with_correction("overpaymnet", top_k=5)
        self.assertEqual(found["corrected_query"], "overpayment")
        self.assertTrue(any("Overpayment" in r["title"] for r in found["results"]))

    def test_exact_search_skips_correction(self):
        found = self.engine.search_with_correction("overpaymnet", top_k=5, correct=False)
        self.assertIsNone(found["corrected_query"])
        self.assertEqual(found["results"], [])

    def test_correct_search_is_unchanged(self):
        found = self.engine.search_with_correction("immediate need", top_k=5)
        self.assertIsNone(found["corrected_query"])
        self.assertTrue(found["results"])


if __name__ == "__main__":
    unittest.main()
