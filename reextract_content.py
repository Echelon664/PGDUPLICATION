#!/usr/bin/env python3
"""
Re-extract the full text of every document's local PDF with pypdf and write it
back to data/documents.json (and the search snippets embedded in
templates/index.html).

Replaces the earlier hand-rolled BT/ET stream parser, which broke word spacing
and capped text at 12,000 characters.

Usage:
    python3 reextract_content.py            # rewrite files
    python3 reextract_content.py --dry-run  # report only
"""
import json
import logging
import os
import re
import sys
import urllib.parse

from pypdf import PdfReader

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS_PATH = os.path.join(ROOT, "data", "documents.json")
PDF_DIR = os.path.join(ROOT, "data", "pdfs")
TEMPLATE_PATH = os.path.join(ROOT, "templates", "index.html")

SECTION_TEXT_CHARS = 4000   # length of sections[0].text, as before
SNIPPET_CHARS = 2500        # length of content_text embedded in the page
MIN_USABLE_CHARS = 200      # below this, treat the PDF as having no text layer
EMBED_MARKER = "const EMBEDDED_DOCS = "


def extract_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    pages = [(page.extract_text() or "") for page in reader.pages]
    text = "\n".join(pages)
    # Re-join words hyphenated across line breaks, then flatten whitespace.
    text = re.sub(r"(?<=[a-z])-\n(?=[a-z])", "", text)
    return re.sub(r"\s+", " ", text).strip()


def pdf_path_for(doc: dict) -> str:
    name = urllib.parse.unquote(os.path.basename(doc.get("local_pdf_url", "")))
    return os.path.join(PDF_DIR, name)


def update_template(docs_by_id: dict) -> int:
    """Refresh content_text in the page's embedded copy. Returns docs updated."""
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html = f.read()
    start = html.index(EMBED_MARKER) + len(EMBED_MARKER)
    embedded, length = json.JSONDecoder().raw_decode(html[start:])
    changed = 0
    for item in embedded:
        doc = docs_by_id.get(item.get("id"))
        if doc and "content_text" in item:
            snippet = doc["content"][:SNIPPET_CHARS]
            if item["content_text"] != snippet:
                item["content_text"] = snippet
                changed += 1
    # "</" must stay escaped so the JSON cannot close the <script> tag.
    new_json = json.dumps(embedded).replace("</", "<\\/")
    with open(TEMPLATE_PATH, "w", encoding="utf-8") as f:
        f.write(html[:start] + new_json + html[start + length:])
    return changed


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    logging.getLogger("pypdf").setLevel(logging.ERROR)

    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)

    updated, kept, failed = 0, [], []
    for doc in docs:
        path = pdf_path_for(doc)
        try:
            text = extract_text(path)
        except Exception as e:  # unreadable or missing PDF: keep what we have
            failed.append((doc["id"], doc["title"], str(e)[:80]))
            continue
        if len(text) < MIN_USABLE_CHARS:
            kept.append((doc["id"], doc["title"], len(text)))
            continue
        doc["content"] = text
        if doc.get("sections"):
            doc["sections"][0]["text"] = text[:SECTION_TEXT_CHARS]
        updated += 1

    print(f"Re-extracted {updated} of {len(docs)} documents.")
    if kept:
        print(f"Kept existing text for {len(kept)} (PDF has little or no text layer):")
        for row in kept:
            print("   ", row)
    if failed:
        print(f"Failed to read {len(failed)} PDFs:")
        for row in failed:
            print("   ", row)

    if dry_run:
        print("Dry run: nothing written.")
        return 0

    with open(DOCS_PATH, "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2)
    n = update_template({d["id"]: d for d in docs})
    print(f"Wrote {DOCS_PATH}")
    print(f"Updated {n} embedded snippets in {TEMPLATE_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
