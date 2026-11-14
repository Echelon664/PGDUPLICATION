"""Offline tests for reading dates out of County PDF text.

Run with:  python3 -m unittest test_pdf_dates
"""

import unittest

import pdf_dates


class PrintedDateTest(unittest.TestCase):
    def test_revision_date_numeric(self):
        text = "CalFresh Program Guide Number Page Household Concept 63-101 1 of 8 Revision Date: 04/01/2023 Background:"
        self.assertEqual(pdf_dates.printed_date(text), ("2023-04-01", "Revision date"))

    def test_revision_date_written_out(self):
        text = "Child Care Provider Requirements Number Page 10-010.C 1 of 8 Revision Date: March 1, 2025 Background:"
        self.assertEqual(pdf_dates.printed_date(text), ("2025-03-01", "Revision date"))

    def test_short_revision_label(self):
        self.assertEqual(pdf_dates.printed_date("Confidentiality 63-353 1 of 2 Revision: 03/01/2021 Background"),
                         ("2021-03-01", "Revision date"))

    def test_issue_date_two_digit_year(self):
        self.assertEqual(pdf_dates.printed_date("CalFresh 18-02 1 of 2 Issue Date: 02/05/18 Background"),
                         ("2018-02-05", "Issue date"))

    def test_effective_date(self):
        self.assertEqual(pdf_dates.printed_date("Number Page 25-02 1 of 2 Effective: 03/01/2025 Background"),
                         ("2025-03-01", "Effective date"))
        self.assertEqual(pdf_dates.printed_date("63-331 1 of 3 Effective Date: June 1, 2019 Background"),
                         ("2019-06-01", "Effective date"))

    def test_revision_beats_effective(self):
        text = "Effective Date: 01/01/2020 something Revision Date: 05/01/2022 Background"
        self.assertEqual(pdf_dates.printed_date(text), ("2022-05-01", "Revision date"))

    def test_effective_in_a_sentence_is_ignored(self):
        self.assertIsNone(pdf_dates.printed_date("Note: Effective January 1, 2014, the Affordable Care Act"))

    def test_impossible_dates_are_rejected(self):
        self.assertIsNone(pdf_dates.printed_date("Revision Date: 13/45/2023"))
        self.assertIsNone(pdf_dates.printed_date("Revision Date: 01/01/1850"))

    def test_only_the_header_is_read(self):
        text = "x" * (pdf_dates.HEADER_CHARS + 10) + " Revision Date: 04/01/2023"
        self.assertIsNone(pdf_dates.printed_date(text))

    def test_no_date(self):
        self.assertIsNone(pdf_dates.printed_date("63-355 Request for Information 63-355.1 Questionable Requests"))
        self.assertIsNone(pdf_dates.printed_date(""))

    def test_revised_date_label(self):
        self.assertEqual(pdf_dates.printed_date("Estate Recovery 16.03 1 of 4 Revised Date: 02/27/2017 Background"),
                         ("2017-02-27", "Revision date"))


class OlderSectionDateTest(unittest.TestCase):
    """Old Medi-Cal sections print no header date."""

    def test_newest_printed_date_anywhere(self):
        text = ("x" * pdf_dates.HEADER_CHARS + " 04.13.01 Revision Date: 08/01/2022 Background ..."
                " 04.13.02 Revision Date: 03/01/2019 Sunset Date: reviewed by 08/31/2025")
        self.assertEqual(pdf_dates.latest_printed_date(text), ("2022-08-01", "Revision date"))

    def test_mpg_letter_month(self):
        text = ("MEDI-CAL PROGRAM GUIDE 9-4-1 6/88 MPG Letter #21 ... MPG LTR 446 (4/01) MEM 50177"
                " ... MEDI-CAL PROGRAM GUIDE 5-17-3 12/03 MPG Letter #526")
        self.assertEqual(pdf_dates.mpg_letter_month(text), "2003-12")
        self.assertEqual(pdf_dates.mpg_letter_month("MPG Letter 755 (05/2012) B. Verifications"), "2012-05")
        self.assertIsNone(pdf_dates.mpg_letter_month("MPG 10.02.03 and MPG 9.9"))

    def test_date_for_prefers_the_newer_of_printed_and_mpg_dates(self):
        mpg_only = {"content": "Article 13 Section 1 ... MPG LTR 76 (11/89) ... MEDI-CAL PROGRAM GUIDE 13-1-2 1/01"}
        self.assertEqual(pdf_dates.date_for(mpg_only), ("2001-01", "Latest MPG letter"))
        combined = {"content": "x" * pdf_dates.HEADER_CHARS + " MPG LTR 569 (01/05) Revision Date: 08/01/2022 Background"}
        self.assertEqual(pdf_dates.date_for(combined), ("2022-08-01", "Latest revision date"))


class StampTest(unittest.TestCase):
    def test_stamp_sets_and_clears_fields(self):
        doc = {"content": "Revision Date: 04/01/2023", "local_pdf_url": ""}
        pdf_dates.stamp(doc)
        self.assertEqual((doc["pdf_date"], doc["pdf_date_label"]), ("2023-04-01", "Revision date"))
        doc["content"] = "no date here"
        pdf_dates.stamp(doc)
        self.assertNotIn("pdf_date", doc)
        self.assertNotIn("pdf_date_label", doc)


if __name__ == "__main__":
    unittest.main()
