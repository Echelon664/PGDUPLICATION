#!/usr/bin/env python3
"""Check and maintain the document summaries in data/summaries/.

Each document has one record:

    "mc-342": {
      "summary": "Explains Social Security Number (SSN) requirements. ...",
      "status": "verified",          # verified | draft | stale
      "pdf_sha256": "9f2c...",       # the PDF the summary was written from
      "updated": "2026-11-13"
    }

    verified  someone compared it with the PDF; it must keep passing the checks
    draft     machine-written or not yet reviewed
    stale     the PDF changed after the summary was written (set by
              county_apply.py, which also stores a fresh "draft_summary")

Usage:
    python3 summaries.py check [--strict]    # CI runs this; --strict also fails on drafts
    python3 summaries.py status              # counts per program and status
    python3 summaries.py show ID             # summary, PDF text and any problems
    python3 summaries.py draft ID [ID ...]   # draft from the PDF's Purpose/Background
    python3 summaries.py verify ID [ID ...]  # mark reviewed after editing the text

To change a summary: edit its "summary" text in data/summaries/<program>.json,
then run `python3 summaries.py verify ID`. Verify refuses text that fails the
checks, such as a dollar amount, percentage, form number or date that does not
appear in the PDF.
"""
import datetime
import re
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List

import catalog

MIN_CHARS = 60
MAX_CHARS = 900
SUMMARY_CHARS = 420
_HEADINGS = (r"Background|Purpose|Policy|Procedures?|Program Impacts?|References?|Sunset Date|"
             r"Approval for Release|Required Action|Impacts?|Forms?|Automation|ACCESS|Quality Control|Summary of Changes")


# ---------------------------------------------------------------- drafting
def extractive_summary(text: str) -> str:
    """The document's own Purpose (else Background) paragraph, cut at a sentence end."""
    for label in ("Purpose", "Background"):
        match = re.search(rf"\b{label}\s*:\s*(.+?)(?=\s(?:{_HEADINGS})\s*:|$)", text, re.S)
        if match and len(match.group(1).strip()) >= 40:
            passage = match.group(1).strip()
            break
    else:
        passage = text
    passage = re.sub(r"\s+", " ", passage).strip()
    if len(passage) <= SUMMARY_CHARS:
        return passage
    cut = passage[:SUMMARY_CHARS]
    end = max(cut.rfind(". "), cut.rfind("; "))
    return cut[:end + 1].strip() if end > 120 else cut.rsplit(" ", 1)[0] + "…"


# ---------------------------------------------------------------- checking
def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def unsupported_facts(summary: str, doc: Dict[str, Any]) -> List[str]:
    """Numbers, amounts, form numbers, codes and dates in the summary that are not in the PDF.

    Any word containing a digit counts (e.g. $2,555, 213%, MC 180's "180",
    SB 184, aid code 8E, 2025-2026). Ranges such as 18-26 pass when each end
    appears in the PDF, and words joined to a number (12-month) only need the number.
    """
    source = _squash(f"{doc.get('title', '')} {doc.get('content', '')}")
    missing = []
    for token in re.findall(r"[$\w][\w$%,./\-]*", summary):
        if not re.search(r"\d", token):
            continue
        token = token.strip(".,;:-/").lower()
        bare = token.strip("$%")
        if len(bare) < 2 or token in source or bare in source:
            continue
        parts = [p.strip("$%") for p in re.split(r"[-/]", token) if re.search(r"\d", p)]
        if len(re.split(r"[-/]", token)) > 1 and all(len(p) < 2 or p in source for p in parts):
            continue
        missing.append(token)
    return missing


def problems_for(doc_id: str, record: Dict[str, Any], doc: Dict[str, Any]) -> List[str]:
    found = []
    text = (record.get("summary") or "").strip()
    status = record.get("status")
    if status not in catalog.STATUSES:
        found.append(f"unknown status {status!r}")
    if not text:
        return found + ["empty summary"]
    if len(text) < MIN_CHARS:
        found.append(f"too short ({len(text)} characters)")
    if len(text) > MAX_CHARS:
        found.append(f"too long ({len(text)} characters)")
    if (doc.get("content") or "").strip():
        missing = unsupported_facts(text, doc)
        if missing:
            found.append("not in the PDF: " + ", ".join(missing))
    if status == "verified":
        current = catalog.pdf_sha256(doc)
        if current and record.get("pdf_sha256") != current:
            found.append("PDF changed since the summary was verified")
    return found


def run_check(strict: bool) -> int:
    docs = {d["id"]: d for d in catalog.load_raw_documents()}
    records = catalog.load_summaries()
    errors: List[str] = []
    warnings: List[str] = []

    for doc_id in docs:
        if doc_id not in records:
            errors.append(f"{doc_id}: no summary record")
    for doc_id in records:
        if doc_id not in docs:
            errors.append(f"{doc_id}: summary record for a document that does not exist")

    seen = defaultdict(list)
    for doc_id, record in records.items():
        if doc_id not in docs:
            continue
        seen[(record.get("summary") or "").strip()].append(doc_id)
        status = record.get("status")
        for problem in problems_for(doc_id, record, docs[doc_id]):
            line = f"{doc_id} [{status}]: {problem}"
            (errors if status == "verified" or strict else warnings).append(line)
        if status == "stale":
            (errors if strict else warnings).append(f"{doc_id} [stale]: PDF changed; review draft_summary and verify")
    for text, ids in seen.items():
        if text and len(ids) > 1:
            errors.append(f"{', '.join(ids)}: identical summaries")

    counts = Counter(r.get("status") for i, r in records.items() if i in docs)
    for line in warnings:
        print("warning: " + line)
    for line in errors:
        print("ERROR: " + line)
    print(f"\n{len(records)} summaries: " + ", ".join(f"{counts[s]} {s}" for s in catalog.STATUSES)
          + f" | {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


# ---------------------------------------------------------------- commands
def _today() -> str:
    return datetime.date.today().isoformat()


def _require(ids: List[str], docs: Dict[str, Any]) -> None:
    unknown = [i for i in ids if i not in docs]
    if not ids or unknown:
        sys.exit(f"Unknown or missing document IDs: {unknown or '(none given)'}")


def cmd_draft(ids: List[str]) -> int:
    docs = {d["id"]: d for d in catalog.load_raw_documents()}
    _require(ids, docs)
    records = catalog.load_summaries()
    for doc_id in ids:
        text = (docs[doc_id].get("content") or "").strip()
        records[doc_id] = {
            "summary": extractive_summary(text) if text else "No text could be extracted from this PDF.",
            "status": "draft",
            "pdf_sha256": catalog.pdf_sha256(docs[doc_id]),
            "updated": _today(),
        }
        print(f"{doc_id}: {records[doc_id]['summary']}")
    catalog.save_summaries(records)
    return 0


def cmd_verify(ids: List[str], force: bool) -> int:
    docs = {d["id"]: d for d in catalog.load_raw_documents()}
    _require(ids, docs)
    records = catalog.load_summaries()
    failed = 0
    for doc_id in ids:
        record = records.get(doc_id)
        if not record:
            print(f"{doc_id}: no summary to verify")
            failed += 1
            continue
        candidate = dict(record, status="verified", pdf_sha256=catalog.pdf_sha256(docs[doc_id]))
        problems = problems_for(doc_id, candidate, docs[doc_id])
        if problems and not force:
            print(f"{doc_id}: not verified: " + "; ".join(problems))
            failed += 1
            continue
        candidate.pop("draft_summary", None)
        candidate["updated"] = _today()
        records[doc_id] = candidate
        print(f"{doc_id}: verified")
    catalog.save_summaries(records)
    return 1 if failed else 0


def cmd_show(doc_id: str) -> int:
    docs = {d["id"]: d for d in catalog.load_raw_documents()}
    _require([doc_id], docs)
    record = catalog.load_summaries().get(doc_id, {})
    doc = docs[doc_id]
    print(f"{doc_id}  {doc['title']}\nPDF: {catalog.pdf_file(doc)}\nStatus: {record.get('status')}\n")
    print("Summary:\n  " + (record.get("summary") or "(none)"))
    if record.get("draft_summary"):
        print("\nDraft from the changed PDF:\n  " + record["draft_summary"])
    problems = problems_for(doc_id, record, doc) if record else []
    print("\nProblems:\n  " + ("\n  ".join(problems) if problems else "none"))
    print("\nPDF text (start):\n  " + (doc.get("content") or "")[:1500])
    return 0


def cmd_status() -> int:
    docs = {d["id"]: d for d in catalog.load_raw_documents()}
    table = defaultdict(Counter)
    for doc_id, record in catalog.load_summaries().items():
        if doc_id in docs:
            table["/".join(docs[doc_id]["programs"])][record.get("status")] += 1
    for program, counts in sorted(table.items()):
        print(f"{program:10} " + "  ".join(f"{s}={counts[s]}" for s in catalog.STATUSES))
    return 0


def main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    command, args = argv[0], argv[1:]
    if command == "check":
        return run_check("--strict" in args)
    if command == "status":
        return cmd_status()
    if command == "show" and len(args) == 1:
        return cmd_show(args[0])
    if command == "draft":
        return cmd_draft(args)
    if command == "verify":
        return cmd_verify([a for a in args if a != "--force"], "--force" in args)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
