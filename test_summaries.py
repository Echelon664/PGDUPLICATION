"""Offline tests for the summary checks and the County sync's summary handling.

Run with:  python3 -m unittest test_summaries
"""
import unittest
from unittest import mock

import county_apply
import summaries


DOC = {"id": "mc-999", "title": "SN 22-09 TB Program Income Limit",
       "content": "Policy: Effective 1/1/2022, the income limit is $1,767. Ages 18 and 26. "
                  "Use form MC 180 for a 12-month period."}


class UnsupportedFactsTest(unittest.TestCase):
    def test_amounts_in_the_pdf_pass(self):
        self.assertEqual(summaries.unsupported_facts("The limit is $1,767 under SN 22-09.", DOC), [])

    def test_amount_not_in_the_pdf_fails(self):
        self.assertEqual(summaries.unsupported_facts("The limit is $1,651.", DOC), ["$1,651"])

    def test_ranges_and_joined_words_pass_when_numbers_appear(self):
        self.assertEqual(summaries.unsupported_facts("Youth 18-26 get 12-month coverage (MC 180).", DOC), [])

    def test_invented_bill_number_fails(self):
        self.assertEqual(summaries.unsupported_facts("Implements SB 184.", DOC), ["184"])


class ProblemsTest(unittest.TestCase):
    def record(self, **kw):
        base = {"summary": "Sets the TB Program income limit at $1,767 effective 1/1/2022.",
                "status": "verified", "pdf_sha256": "abc"}
        base.update(kw)
        return base

    def test_clean_verified_record(self):
        with mock.patch("catalog.pdf_sha256", return_value="abc"):
            self.assertEqual(summaries.problems_for("mc-999", self.record(), DOC), [])

    def test_changed_pdf_is_reported_for_verified(self):
        with mock.patch("catalog.pdf_sha256", return_value="def"):
            self.assertIn("PDF changed since the summary was verified",
                          summaries.problems_for("mc-999", self.record(), DOC))

    def test_empty_and_short(self):
        with mock.patch("catalog.pdf_sha256", return_value="abc"):
            self.assertEqual(summaries.problems_for("mc-999", self.record(summary=""), DOC), ["empty summary"])
            self.assertIn("too short (5 characters)",
                          summaries.problems_for("mc-999", self.record(summary="Short"), DOC))


class CountyApplySummaryTest(unittest.TestCase):
    def applier(self, records):
        applier = object.__new__(county_apply.Applier)
        applier.summaries = records
        applier.review = []
        return applier

    def test_replaced_pdf_marks_summary_stale_and_keeps_text(self):
        records = {"mc-999": {"summary": "Reviewed text.", "status": "verified", "pdf_sha256": "old"}}
        with mock.patch("catalog.pdf_sha256", return_value="new"):
            self.applier(records).update_summary(DOC, "Draft from the new PDF.")
        self.assertEqual(records["mc-999"]["summary"], "Reviewed text.")
        self.assertEqual(records["mc-999"]["status"], "stale")
        self.assertEqual(records["mc-999"]["draft_summary"], "Draft from the new PDF.")

    def test_new_document_gets_a_draft(self):
        records = {}
        with mock.patch("catalog.pdf_sha256", return_value="new"):
            self.applier(records).update_summary(DOC, "Draft text.")
        self.assertEqual(records["mc-999"]["status"], "draft")
        self.assertEqual(records["mc-999"]["summary"], "Draft text.")

    def test_unchanged_pdf_leaves_summary_alone(self):
        records = {"mc-999": {"summary": "Reviewed text.", "status": "verified", "pdf_sha256": "same"}}
        with mock.patch("catalog.pdf_sha256", return_value="same"):
            self.applier(records).update_summary(DOC, "Draft.")
        self.assertEqual(records["mc-999"], {"summary": "Reviewed text.", "status": "verified", "pdf_sha256": "same"})


if __name__ == "__main__":
    unittest.main()
