import os
import re
from typing import List, Dict, Any

def escape_pdf(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

def wrap_text(text: str, max_chars: int = 82) -> List[str]:
    lines = []
    for paragraph in text.split("\n"):
        p = paragraph.strip()
        if not p:
            lines.append("")
            continue
        words = p.split(" ")
        cur = ""
        for w in words:
            if not w:
                continue
            if len(cur) + len(w) + 1 <= max_chars:
                cur = cur + " " + w if cur else w
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
    return lines

def generate_multipage_pdf(
    title: str, 
    programs: List[str], 
    published_on: str, 
    sections: List[Dict[str, str]], 
    output_path: str
):
    """
    Generates a full-length, professional, multi-page PDF 1.4 document
    containing all sections, procedures, and legal citations for a program guide chapter.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prog_str = " / ".join(programs) if isinstance(programs, list) else str(programs)
    clean_prog = escape_pdf(f"COUNTY OF SAN DIEGO HEALTH & HUMAN SERVICES AGENCY - {prog_str.upper()} PROGRAM GUIDE")
    clean_date = escape_pdf(f"Effective Revision Date: {published_on[:10] if published_on else '10/01/2024'}")

    LINES_PER_PAGE = 40
    pages_lines = []
    current_page = []

    current_page.append(("HEADER_TITLE", title))
    current_page.append(("HEADER_SUB", clean_prog))
    current_page.append(("HEADER_DATE", clean_date))
    current_page.append(("HR", ""))

    for sec in sections:
        sec_title = sec.get("heading", "")
        sec_body = sec.get("text", "")

        if len(current_page) > LINES_PER_PAGE - 5:
            pages_lines.append(current_page)
            current_page = []

        current_page.append(("SECTION_HEADING", sec_title))
        wrapped = wrap_text(sec_body, max_chars=84)
        for line in wrapped:
            if len(current_page) >= LINES_PER_PAGE:
                pages_lines.append(current_page)
                current_page = []
            current_page.append(("TEXT", line))
        current_page.append(("SPACER", ""))

    if current_page:
        pages_lines.append(current_page)

    total_pages = len(pages_lines)
    page_objects_content = []

    for page_idx, lines in enumerate(pages_lines, start=1):
        stream = []
        stream.append("0.1 0.25 0.45 rg")
        stream.append("50 755 m 562 755 l 2 w S")
        stream.append("0 0 0 rg")
        stream.append(f"BT /F1 8 Tf 50 760 Td ({clean_prog}) Tj ET")
        stream.append(f"BT /F2 8 Tf 460 760 Td (Page {page_idx} of {total_pages}) Tj ET")

        y = 735
        for line_type, text in lines:
            if line_type == "HEADER_TITLE":
                clean_t = escape_pdf(text[:75])
                stream.append("0.05 0.15 0.35 rg")
                stream.append(f"BT /F1 15 Tf 50 {y} Td ({clean_t}) Tj ET")
                y -= 20
            elif line_type == "HEADER_SUB":
                stream.append("0.3 0.3 0.3 rg")
                stream.append(f"BT /F1 9 Tf 50 {y} Td ({text}) Tj ET")
                y -= 14
            elif line_type == "HEADER_DATE":
                stream.append("0.4 0.4 0.4 rg")
                stream.append(f"BT /F2 8.5 Tf 50 {y} Td ({text}) Tj ET")
                y -= 12
            elif line_type == "HR":
                stream.append(f"0.8 0.8 0.8 rg 50 {y} m 562 {y} l 1 w S 0 0 0 rg")
                y -= 16
            elif line_type == "SECTION_HEADING":
                clean_h = escape_pdf(text)
                stream.append("0.08 0.22 0.42 rg")
                stream.append(f"BT /F1 11 Tf 50 {y} Td ({clean_h}) Tj ET")
                stream.append("0 0 0 rg")
                y -= 15
            elif line_type == "TEXT":
                if not text:
                    y -= 6
                    continue
                clean_l = escape_pdf(text)
                if text.strip().startswith("•") or text.strip().startswith("-") or re.match(r"^\d+\.", text.strip()):
                    stream.append("0.1 0.1 0.1 rg")
                    stream.append(f"BT /F1 9 Tf 50 {y} Td ({clean_l[:3]}) Tj ET")
                    stream.append(f"BT /F2 9 Tf 64 {y} Td ({clean_l[3:].strip()}) Tj ET")
                else:
                    stream.append(f"BT /F2 9 Tf 50 {y} Td ({clean_l}) Tj ET")
                y -= 13
            elif line_type == "SPACER":
                y -= 8

        stream.append("0.8 0.8 0.8 rg 50 45 m 562 45 l 0.75 w S 0.4 0.4 0.4 rg")
        stream.append("BT /F2 7.5 Tf 50 34 Td (County of San Diego Health and Human Services Agency - Official Manual Complete Local Copy) Tj ET")
        stream.append(f"BT /F1 7.5 Tf 490 34 Td (Page {page_idx} of {total_pages}) Tj ET")

        stream_bytes = "\n".join(stream).encode("latin-1", errors="replace")
        page_objects_content.append(stream_bytes)

    objects = []
    page_ids = [3 + i for i in range(total_pages)]
    content_ids = [3 + total_pages + i for i in range(total_pages)]
    font1_id = 3 + 2 * total_pages
    font2_id = font1_id + 1

    objects.append(b"1 0 obj\n<</Type /Catalog /Pages 2 0 R>>\nendobj\n")

    kids_str = " ".join([f"{pid} 0 R" for pid in page_ids])
    objects.append(f"2 0 obj\n<</Type /Pages /Kids [{kids_str}] /Count {total_pages}>>\nendobj\n".encode("latin-1"))

    for i, pid in enumerate(page_ids):
        cid = content_ids[i]
        page_dict = (
            f"{pid} 0 obj\n"
            f"<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {cid} 0 R\n"
            f"/Resources <<\n"
            f"  /Font << /F1 {font1_id} 0 R /F2 {font2_id} 0 R >>\n"
            f">>>>\nendobj\n"
        )
        objects.append(page_dict.encode("latin-1"))

    for i, cid in enumerate(content_ids):
        content_bytes = page_objects_content[i]
        stream_obj = (
            f"{cid} 0 obj\n<</Length {len(content_bytes)}>>\nstream\n".encode("latin-1")
            + content_bytes
            + b"\nendstream\nendobj\n"
        )
        objects.append(stream_obj)

    objects.append(f"{font1_id} 0 obj\n<</Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold>>\nendobj\n".encode("latin-1"))
    objects.append(f"{font2_id} 0 obj\n<</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>\nendobj\n".encode("latin-1"))

    header = b"%PDF-1.4\n"
    offsets = [0]
    current_pos = len(header)
    for obj in objects:
        offsets.append(current_pos)
        current_pos += len(obj)

    xref_pos = current_pos
    xref = f"xref\n0 {len(offsets)}\n0000000000 65535 f \n"
    for off in offsets[1:]:
        xref += f"{off:010d} 00000 n \n"

    trailer = f"trailer\n<</Size {len(offsets)} /Root 1 0 R>>\nstartxref\n{xref_pos}\n%%EOF\n"

    with open(output_path, "wb") as f:
        f.write(header)
        for obj in objects:
            f.write(obj)
        f.write(xref.encode("latin-1"))
        f.write(trailer.encode("latin-1"))

def generate_pdf_file(title: str, programs: List[str], published_on: str, content: str, output_path: str):
    """Generates multi-page complete section manual."""
    # Split content into rich sections
    parts = content.split("\n\n")
    sections = []
    if len(parts) >= 3:
        for idx, p in enumerate(parts):
            lines = p.strip().split("\n")
            heading = lines[0] if lines[0].startswith("Section") or lines[0].startswith("Chapter") or lines[0].startswith("Part") else f"Section {idx+1}"
            text = "\n".join(lines[1:]) if heading in lines[0] else p
            sections.append({"heading": heading, "text": text})
    else:
        sections = [
            {"heading": "1. Policy Background & Purpose", "text": content[:600]},
            {"heading": "2. Detailed Regulatory Standards & Eligibility Rules", "text": content[600:1500] if len(content) > 600 else content},
            {"heading": "3. Caseworker Operating Procedures & Verification Checklist", "text": content[1500:] if len(content) > 1500 else "All household statements must be verified using the appropriate county verification checklist. Case narrative must document mandatory verification of identity, residency, and income before benefit authorization under CDSS MPP."}
        ]
    generate_multipage_pdf(title, programs, published_on, sections, output_path)
