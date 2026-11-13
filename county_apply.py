"""Bring the stored catalog in line with the County site.

Reads the latest FULL report from county_sync.py and applies it to
data/documents.json and data/pdfs/:

    changed        download the County's current file and attach it
    missing        fill catalog stubs, and add entries for County files that
                   have none (reusing a PDF already on disk when it matches)
    not_on_county  remove the entry (only with --remove-stale)
    identical      record the County file ID, direct link and publish date

Text is re-extracted from each new PDF. Summaries live in data/summaries/ and
are never overwritten here: a replaced PDF marks its summary "stale" and stores
a draft from the document's own Purpose/Background paragraph beside it, and a
new document gets that paragraph as a "draft" summary. Review them with
summaries.py; they are listed at the end.

Usage:
    python3 county_sync.py full                   # fresh report first
    python3 county_apply.py --dry-run             # show what would change
    python3 county_apply.py [--remove-stale]
    python3 summaries.py check                    # list summaries to review
    python3 county_sync.py full                   # confirm
"""

import datetime
import json
import logging
import os
import re
import sys
import urllib.parse
from typing import Any, Dict, List, Optional

import catalog
import county_sync as cs
import pdf_dates
from summaries import extractive_summary

SECTION_TEXT_CHARS = 4000


def extract_text(pdf_path: str) -> str:
    from pypdf import PdfReader  # only needed when applying changes
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    reader = PdfReader(pdf_path)
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    text = re.sub(r"(?<=[a-z])-\n(?=[a-z])", "", text)
    return re.sub(r"\s+", " ", text).strip()


def safe_filename(title: str, file_id: str) -> str:
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', " ", title.replace("_", " "))
    name = re.sub(r"\s+", " ", name).strip(" .")[:120] or "document"
    return f"{name} [{file_id}].pdf"


def pdf_url(filename: str) -> str:
    return "/pdfs/" + urllib.parse.quote(filename)


def clean_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title.replace("_", " ")).strip()
    return re.sub(r"\.(docx?|pdf)$", "", title, flags=re.I)


class Applier:
    def __init__(self, dry_run: bool, remove_stale: bool):
        self.dry_run = dry_run
        self.remove_stale = remove_stale
        self.client = cs.CountyClient()
        self.log: List[str] = []
        self.review: List[str] = []
        with open(cs.DOCS_PATH, "r", encoding="utf-8") as f:
            self.docs: List[Dict[str, Any]] = json.load(f)
        self.by_id = {d["id"]: d for d in self.docs}
        self.summaries = catalog.load_summaries()
        self.stored = cs.hash_stored_files()
        manifest = cs._read_json(cs.MANIFEST_PATH) or {}
        self.manifest: Dict[str, Dict[str, Any]] = manifest.get("files", {})

    # -- files
    def obtain_pdf(self, row: Dict[str, Any]) -> Optional[str]:
        """File name in data/pdfs holding the County file for this row."""
        file_id = row["county_file_id"]
        known_hash = (self.manifest.get(file_id) or {}).get("hash")
        if known_hash and known_hash in self.stored:
            return self.stored[known_hash]
        filename = safe_filename(row["county_title"], file_id)
        if self.dry_run:
            return filename
        data = self.client.fetch_file(file_id)
        if not data.startswith(b"%PDF"):
            self.log.append(f"SKIPPED {file_id} {row['county_title']}: County file is not a PDF")
            return None
        with open(os.path.join(cs.PDF_DIR, filename), "wb") as f:
            f.write(data)
        self.stored[cs.content_hash(data)] = filename
        return filename

    def attach(self, doc: Dict[str, Any], row: Dict[str, Any], filename: str, heading: str) -> None:
        doc["local_pdf_url"] = pdf_url(filename)
        doc.pop("source_missing", None)
        self.stamp(doc, row)
        if self.dry_run:
            return
        try:
            text = extract_text(os.path.join(cs.PDF_DIR, filename))
        except Exception as exc:  # e.g. an AES-protected PDF without the cryptography package
            text = ""
            self.log.append(f"NO TEXT for {doc['id']}: {str(exc)[:90]}")
        doc["content"] = text
        doc["sections"] = [{"heading": heading, "text": text[:SECTION_TEXT_CHARS]}]
        pdf_dates.stamp(doc)
        self.update_summary(doc, extractive_summary(text) if text else "No text could be extracted from this PDF.")

    def update_summary(self, doc: Dict[str, Any], draft: str) -> None:
        """New document: draft summary. Replaced PDF: keep the summary, mark it stale."""
        record = self.summaries.get(doc["id"])
        digest = catalog.pdf_sha256(doc)
        if record and record.get("summary") and record.get("pdf_sha256") != digest:
            record.update(status="stale", draft_summary=draft)
            self.review.append(f"{doc['id']} | {doc['title']} (PDF changed; summary marked stale)\n      draft: {draft}")
        elif not record or not record.get("summary"):
            self.summaries[doc["id"]] = {"summary": draft, "status": "draft", "pdf_sha256": digest,
                                         "updated": datetime.date.today().isoformat()}
            self.review.append(f"{doc['id']} | {doc['title']} (new; draft summary)\n      {draft}")

    @staticmethod
    def stamp(doc: Dict[str, Any], row: Dict[str, Any]) -> None:
        doc["county_file_id"] = row["county_file_id"]
        doc["official_url"] = row["county_url"]
        if row.get("county_published_on") and not row["county_published_on"].startswith("1900"):
            doc["published_on"] = row["county_published_on"]

    # -- actions
    def new_entry(self, row: Dict[str, Any]) -> Dict[str, Any]:
        program = row["program"]
        prefix = {"CalFresh": "cf", "CalWORKs": "cw", "Medi-Cal": "mc"}[program]
        numbers = [int(d["id"].split("-")[1]) for d in self.docs
                   if d["id"].startswith(prefix + "-") and d["id"].split("-")[1].isdigit()]
        title = clean_title(row["county_title"])
        folder = row["county_path"].split(" / ")
        is_notice = folder[0].strip().lower().startswith("special notice")
        # Reuse the chapter metadata of an existing entry in the same County folder.
        if is_notice:
            sibling = next((d for d in self.docs if program in d["programs"]
                            and "special notice" in d.get("category", "").lower()), None)
            if re.match(r"\d\d-\d\d\b", title):
                title = "SN " + title
            number = re.match(r"SN[ -]?(\d\d-\d\d)", title)
            section_num = f"SN {number.group(1)}" if number else "SN"
            section_title = re.sub(r"^SN[ -]?\d\d-\d\d[\s\-–]*", "", title).strip() or title
        else:
            chapter_name = folder[-1].strip()
            sibling = next((d for d in self.docs if program in d["programs"]
                            and cs.normalize_title(d.get("chapter", "")) == cs.normalize_title(chapter_name)), None)
            section_num = sibling.get("section_num", "") if sibling else ""
            section_title = sibling.get("section_title", "") if sibling else chapter_name
        doc: Dict[str, Any] = {
            "id": f"{prefix}-{max(numbers, default=-1) + 1:03d}",
            "title": title,
            "chapter": sibling["chapter"] if sibling else folder[-1].strip(),
            "programs": [program],
            "published_on": "",
            "file_type": "PDF",
            "local_pdf_url": "",
            "official_url": row["county_url"],
            "content": "",
            "sections": [],
            "section_num": section_num,
            "section_title": section_title,
            "category": sibling.get("category", "") if sibling else folder[-1].strip(),
            "category_desc": sibling.get("category_desc", "") if sibling else "",
            "order": sibling.get("order", 99) if sibling else 99,
        }
        if sibling and sibling.get("category_id"):
            doc["category_id"] = sibling["category_id"]
        # Keep each program's entries together: insert after its last entry.
        last = max((i for i, d in enumerate(self.docs) if program in d["programs"]), default=len(self.docs) - 1)
        self.docs.insert(last + 1, doc)
        self.by_id[doc["id"]] = doc
        return doc

    @staticmethod
    def heading_for(doc: Dict[str, Any]) -> str:
        if "special notice" in doc.get("category", "").lower():
            return "Special Notices"
        return f"{doc.get('section_num', '')}{doc.get('section_title', '')}" or doc.get("chapter", "")

    def run(self, report: Dict[str, Any]) -> None:
        groups = report["groups"]

        for row in groups["identical"]:
            doc = self.by_id.get(row["doc_id"])
            if doc:
                self.stamp(doc, row)
        self.log.append(f"Recorded County ID, link and publish date on {len(groups['identical'])} matching entries")

        for row in groups["changed"] + groups["missing"]:
            doc = self.by_id.get(row["doc_id"]) if row.get("doc_id") else None
            filename = self.obtain_pdf(row)
            if not filename:
                continue
            if doc is None:
                doc = self.new_entry(row)
                action = "ADDED"
            else:
                action = "FILLED" if doc.get("source_missing") or not doc.get("local_pdf_url") else "REPLACED"
            self.attach(doc, row, filename, self.heading_for(doc))
            self.log.append(f"{action} {doc['id']} {doc['title']}  <-  {filename}")

        for row in groups["not_on_county"]:
            if not self.remove_stale:
                self.log.append(f"LEFT {row['doc_id']} {row['doc_title']} (not on the County site; use --remove-stale)")
                continue
            doc = self.by_id.pop(row["doc_id"], None)
            if doc:
                self.docs.remove(doc)
                self.summaries.pop(doc["id"], None)
                self.log.append(f"REMOVED {row['doc_id']} {row['doc_title']} (not on the County site)")

        if groups.get("mislabelled"):
            self.log.append(f"NOT HANDLED: {len(groups['mislabelled'])} mislabelled entries need a manual look")

        if not self.dry_run:
            tmp = cs.DOCS_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.docs, f, indent=2)
            os.replace(tmp, cs.DOCS_PATH)
            catalog.save_summaries(self.summaries)


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    report = cs.load_report()
    if not report or report.get("mode") != "full":
        sys.exit("Run a full scan first: python3 county_sync.py full")
    applier = Applier(dry_run, "--remove-stale" in sys.argv)
    try:
        applier.run(report)
    except cs.CountyError as exc:
        sys.exit(f"Stopped: {exc}")
    print("\n".join(applier.log))
    if applier.review:
        print("\nSummaries taken from the documents (review these):")
        for item in applier.review:
            print("  " + item)
    print("\nDry run: nothing written." if dry_run
          else "\nDone. Now run: python3 summaries.py check && python3 county_sync.py full")
    return 0


if __name__ == "__main__":
    sys.exit(main())
