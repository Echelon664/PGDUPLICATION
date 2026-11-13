"""Offline tests for the County comparison logic.

Run with:  python3 -m unittest test_county_sync
"""

import os
import unittest

import county_sync as cs


def doc(doc_id, title, h, program="CalFresh", source_missing=False):
    return {"id": doc_id, "title": title, "program": program, "chapter": "",
            "filename": f"{title}.pdf" if h else "", "hash": h, "size": 1 if h else None,
            "source_missing": source_missing}


def county(file_id, title, h=None, program="CalFresh", **extra):
    entry = {"file_id": file_id, "title": title, "program": program, "path": ["Chapters"],
             "published_on": "2024-01-01T00:00:00Z"}
    if h:
        entry["hash"] = h
    entry.update(extra)
    return entry


class ContentHashTest(unittest.TestCase):
    def test_trailer_id_is_ignored(self):
        a = b"%PDF-1.7 body /Root 2 0 R/ID[<AAAA><AAAA>]/Filter end"
        b = b"%PDF-1.7 body /Root 2 0 R/ID[<BBBB><BBBB>]/Filter end"
        self.assertEqual(cs.content_hash(a), cs.content_hash(b))

    def test_body_change_is_detected(self):
        a = b"%PDF-1.7 body /ID[<AAAA><AAAA>] end"
        b = b"%PDF-1.7 BODY /ID[<AAAA><AAAA>] end"
        self.assertNotEqual(cs.content_hash(a), cs.content_hash(b))

    def test_title_normalization(self):
        self.assertEqual(cs.normalize_title("63-113_Authorized_Representatives"),
                         cs.normalize_title("63-113 Authorized Representatives"))


class CompareFullTest(unittest.TestCase):
    def groups(self, county_files, docs):
        result = cs.compare(county_files, docs, "full")
        return result, {k: [r.get("county_file_id") or r.get("doc_id") for r in v]
                        for k, v in result["groups"].items()}

    def test_all_identical_is_in_sync(self):
        result, g = self.groups([county("1", "A", "h1"), county("2", "B", "h2")],
                                [doc("d1", "A", "h1"), doc("d2", "B", "h2")])
        self.assertTrue(result["in_sync"])
        self.assertEqual(g["identical"], ["1", "2"])

    def test_changed_missing_and_removed(self):
        result, g = self.groups(
            [county("1", "A", "new"), county("2", "B", "h2"), county("3", "C", "h3")],
            [doc("d1", "A", "old"), doc("d2", "B", "h2"), doc("d9", "Gone", "h9")])
        self.assertFalse(result["in_sync"])
        self.assertEqual(g["changed"], ["1"])
        self.assertEqual(g["identical"], ["2"])
        self.assertEqual(g["missing"], ["3"])
        self.assertEqual(g["not_on_county"], ["d9"])

    def test_stub_entry_counts_as_missing(self):
        _, g = self.groups([county("1", "A", "h1")], [doc("d1", "A", None, source_missing=True)])
        self.assertEqual(g["missing"], ["1"])
        self.assertEqual(g["not_on_county"], [])

    def test_same_file_under_other_title_is_identical(self):
        _, g = self.groups([county("1", "63-113_Authorized_Reps", "h1")], [doc("d1", "Auth Reps", "h1")])
        self.assertEqual(g["identical"], ["1"])

    def test_file_stored_under_wrong_entry(self):
        _, g = self.groups([county("1", "A", "h1"), county("2", "B", "h2")],
                           [doc("d1", "A", "h2"), doc("d2", "B", "h1")])
        self.assertEqual(sorted(g["mislabelled"]), ["1", "2"])
        self.assertEqual(g["identical"], [])

    def test_programs_do_not_cross_match(self):
        _, g = self.groups([county("1", "A", "h1", program="CalWORKs")], [doc("d1", "A", "h1")])
        self.assertEqual(g["missing"], ["1"])
        self.assertEqual(g["not_on_county"], ["d1"])

    def test_download_error_is_not_reported_as_removed(self):
        result, g = self.groups([county("1", "A", error="timeout")], [doc("d1", "A", "h1")])
        self.assertEqual(g["errors"], ["1"])
        self.assertEqual(g["not_on_county"], [])
        self.assertFalse(result["in_sync"])


class CompareQuickTest(unittest.TestCase):
    def test_quick_uses_last_full_scan(self):
        prev = {"published_on": "2024-01-01T00:00:00Z", "hash": "h1", "doc_id": "d1"}
        files = [
            county("1", "A", previous=prev, verified=prev),
            county("2", "B", previous={"published_on": "2023-01-01T00:00:00Z", "hash": "h2", "doc_id": "d2"}),
            county("3", "C"),
        ]
        result = cs.compare(files, [doc("d1", "A", "h1"), doc("d2", "B", "h2"), doc("d3", "C", "h3")], "quick")
        g = {k: [r["county_file_id"] for r in v] for k, v in result["groups"].items() if k != "not_on_county"}
        self.assertEqual(g["identical"], ["1"])
        self.assertEqual(g["unverified"], ["2", "3"])
        self.assertFalse(result["in_sync"])  # a quick scan never certifies 1:1

    def test_quick_notices_locally_replaced_pdf(self):
        prev = {"published_on": "2024-01-01T00:00:00Z", "hash": "h1", "doc_id": "d1"}
        result = cs.compare([county("1", "A", previous=prev, verified=prev)], [doc("d1", "A", "edited")], "quick")
        self.assertEqual(len(result["groups"]["unverified"]), 1)


class AdminTokenTest(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get("ADMIN_TOKEN")

    def tearDown(self):
        if self._old is None:
            os.environ.pop("ADMIN_TOKEN", None)
        else:
            os.environ["ADMIN_TOKEN"] = self._old

    def test_disabled_without_token(self):
        os.environ.pop("ADMIN_TOKEN", None)
        self.assertFalse(cs.admin_enabled())
        self.assertFalse(cs.check_admin(""))
        self.assertFalse(cs.check_admin("anything"))

    def test_token_must_match(self):
        os.environ["ADMIN_TOKEN"] = "example-token"
        self.assertTrue(cs.check_admin("example-token"))
        self.assertFalse(cs.check_admin("wrong"))
        self.assertFalse(cs.check_admin(None))


if __name__ == "__main__":
    unittest.main()
