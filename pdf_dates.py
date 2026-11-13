"""Date each catalog entry from its own PDF.

Every entry gets two fields:

    pdf_date        ISO date (YYYY-MM-DD)
    pdf_date_label  where the date came from

The date printed in the document is preferred (Revision date, Issue date,
Effective date). Documents that print none (charts, Q&As, scanned pages) fall
back to the date stored in the PDF file itself ("PDF file date").

Usage:
    python3 pdf_dates.py            # stamp data/documents.json
    python3 pdf_dates.py --dry-run  # report only
"""

import datetime
import json
import os
import re
import sys
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_PATH = os.path.join(BASE_DIR, "data", "documents.json")
PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")

# County documents print their date in the header block on page one.
HEADER_CHARS = 1500

_MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
_DATE = (r"(?:(?P<m>\d{1,2})\s*/\s*(?P<d>\d{1,2})\s*/\s*(?P<y>\d{4}|\d{2})(?!\d)"
         r"|(?P<mon>[A-Za-z]{3,9})\.?\s+(?P<d2>\d{1,2})\s*,?\s*(?P<y2>\d{4}))")

# Most specific first: a revision date says more about currency than an effective date.
_LABELS: List[Tuple[str, str]] = [
    (r"Revision\s+Date|Revision|Revised", "Revision date"),
    (r"Issue\s+Date|Date\s+Issued", "Issue date"),
    (r"Effective\s+Date", "Effective date"),
    (r"Effective(?=\s*:)", "Effective date"),
]


def _valid(year: int, month: int, day: int) -> Optional[str]:
    if year < 100:
        year += 2000 if year < 70 else 1900
    try:
        value = datetime.date(year, month, day)
    except ValueError:
        return None
    if not 1990 <= value.year <= datetime.date.today().year + 2:
        return None
    return value.isoformat()


def _parse(match: "re.Match[str]") -> Optional[str]:
    if match.group("m"):
        return _valid(int(match.group("y")), int(match.group("m")), int(match.group("d")))
    month = _MONTHS.get(match.group("mon")[:3].lower())
    if not month:
        return None
    return _valid(int(match.group("y2")), month, int(match.group("d2")))


def printed_date(text: str) -> Optional[Tuple[str, str]]:
    """(ISO date, label) for the date printed in the document header, if any."""
    head = (text or "")[:HEADER_CHARS]
    for pattern, label in _LABELS:
        for match in re.finditer(rf"\b(?:{pattern})\s*:?\s*{_DATE}", head, re.I):
            iso = _parse(match)
            if iso:
                return iso, label
    return None


def file_date(pdf_path: str) -> Optional[str]:
    """ISO date stored in the PDF's own metadata (modified, else created)."""
    try:
        from pypdf import PdfReader
        metadata = PdfReader(pdf_path).metadata or {}
    except Exception:
        return None
    for key in ("/ModDate", "/CreationDate"):
        match = re.match(r"D:(\d{4})(\d{2})(\d{2})", str(metadata.get(key) or ""))
        if match:
            iso = _valid(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            if iso:
                return iso
    return None


def date_for(doc: Dict[str, Any], pdf_dir: str = PDF_DIR) -> Optional[Tuple[str, str]]:
    found = printed_date(doc.get("content", ""))
    if found:
        return found
    url = doc.get("local_pdf_url") or ""
    if url:
        iso = file_date(os.path.join(pdf_dir, urllib.parse.unquote(os.path.basename(url))))
        if iso:
            return iso, "PDF file date"
    return None


def stamp(doc: Dict[str, Any], pdf_dir: str = PDF_DIR) -> None:
    found = date_for(doc, pdf_dir)
    if found:
        doc["pdf_date"], doc["pdf_date_label"] = found
    else:
        doc.pop("pdf_date", None)
        doc.pop("pdf_date_label", None)


def main() -> int:
    import logging
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)
    counts: Dict[str, int] = {}
    for doc in docs:
        stamp(doc)
        label = doc.get("pdf_date_label", "No date found")
        counts[label] = counts.get(label, 0) + 1
    for label, count in sorted(counts.items(), key=lambda item: -item[1]):
        print(f"  {count:4d}  {label}")
    if "--dry-run" in sys.argv:
        print("Dry run: nothing written.")
        return 0
    with open(DOCS_PATH, "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2)
    print(f"Stamped {len(docs)} entries. Now run: python3 generate_preview.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
