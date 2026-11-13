"""Load the document catalog together with its summaries.

The catalog lives in two places:

    data/documents.json      PDF metadata and extracted text (written by the
                             County sync and the crawler)
    data/summaries/*.json    one reviewed summary per document, per program
                             (written only through summaries.py)

Everything that shows or searches summaries reads them through
load_documents(), so there is exactly one copy of each summary.
"""
import hashlib
import json
import os
import subprocess
import sys
import urllib.parse
from typing import Any, Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_PATH = os.path.join(BASE_DIR, "data", "documents.json")
PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")
SUMMARIES_DIR = os.path.join(BASE_DIR, "data", "summaries")

# Document ID prefix -> summaries file.
SUMMARY_FILES = {
    "cf": "calfresh.json",
    "cw": "calworks.json",
    "mc": "medi-cal.json",
}

STATUSES = ("verified", "draft", "stale")

PAGE_PATH = os.path.join(BASE_DIR, "templates", "index.html")


def summary_file_for(doc_id: str) -> str:
    prefix = doc_id.split("-", 1)[0]
    if prefix not in SUMMARY_FILES:
        raise ValueError(f"No summaries file for document ID {doc_id!r}")
    return os.path.join(SUMMARIES_DIR, SUMMARY_FILES[prefix])


def summary_paths() -> List[str]:
    return [os.path.join(SUMMARIES_DIR, name) for name in SUMMARY_FILES.values()]


def load_summaries() -> Dict[str, Dict[str, Any]]:
    """All summary records keyed by document ID."""
    records: Dict[str, Dict[str, Any]] = {}
    for path in summary_paths():
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                records.update(json.load(f))
    return records


def save_summaries(records: Dict[str, Dict[str, Any]]) -> None:
    """Write records back, one file per program, in stable order."""
    os.makedirs(SUMMARIES_DIR, exist_ok=True)
    by_file: Dict[str, Dict[str, Any]] = {path: {} for path in summary_paths()}
    for doc_id in sorted(records, key=_id_sort_key):
        by_file[summary_file_for(doc_id)][doc_id] = records[doc_id]
    for path, group in by_file.items():
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(group, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)


def load_raw_documents(docs_path: str = DOCS_PATH) -> List[Dict[str, Any]]:
    with open(docs_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_documents(docs_path: str = DOCS_PATH) -> List[Dict[str, Any]]:
    """Documents with "summary" and "summary_status" filled from the store."""
    docs = load_raw_documents(docs_path)
    records = load_summaries()
    for doc in docs:
        record = records.get(doc["id"]) or {}
        doc["summary"] = record.get("summary", "")
        doc["summary_status"] = record.get("status", "")
    return docs


def source_mtime(docs_path: str = DOCS_PATH) -> float:
    """Latest change to the documents or any summaries file."""
    paths = [docs_path] + [p for p in summary_paths() if os.path.exists(p)]
    return max(os.path.getmtime(p) for p in paths)


def ensure_page() -> None:
    """Build templates/index.html when it is missing or older than the data.

    The page embeds the catalog, so it is generated, never committed. The
    Docker build creates it; this covers local runs and edited summaries.
    """
    if os.path.exists(PAGE_PATH) and os.path.getmtime(PAGE_PATH) >= source_mtime():
        return
    subprocess.run([sys.executable, os.path.join(BASE_DIR, "generate_preview.py")],
                   cwd=BASE_DIR, check=True, stdout=subprocess.DEVNULL)


def pdf_file(doc: Dict[str, Any]) -> Optional[str]:
    url = doc.get("local_pdf_url") or ""
    if not url.startswith("/pdfs/"):
        return None
    path = os.path.join(PDF_DIR, urllib.parse.unquote(url[len("/pdfs/"):]))
    return path if os.path.isfile(path) else None


def pdf_sha256(doc: Dict[str, Any]) -> Optional[str]:
    path = pdf_file(doc)
    if not path:
        return None
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _id_sort_key(doc_id: str):
    prefix, _, number = doc_id.partition("-")
    return (prefix, int(number) if number.isdigit() else 0, doc_id)
