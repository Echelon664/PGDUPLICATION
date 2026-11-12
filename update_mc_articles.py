#!/usr/bin/env python3
import json
import re
import os

DOCS_PATH = "/Users/echelon619/.gemini/antigravity/scratch/sd-benefits-search/data/documents.json"
PART1_PATH = "/Users/echelon619/.gemini/antigravity/brain/cecb2a45-dbe4-4639-bcf4-7ffbb562b7ad/browser_sandbox/outputs/step_29.json"
PART2_PATH = "/Users/echelon619/.gemini/antigravity/brain/cecb2a45-dbe4-4639-bcf4-7ffbb562b7ad/browser_sandbox/outputs/step_27.json"

ARTICLE_DESCRIPTIONS = {
    "ARTICLE 01": ("ARTICLE 01 - DEFINITIONS", "Official Medi-Cal terms, beneficiary definitions, and program concepts", 1),
    "ARTICLE 02": ("ARTICLE 02 - CONFIDENTIALITY", "Safeguarding Medi-Cal case records and confidential health information", 2),
    "ARTICLE 03": ("ARTICLE 03 - COUNTY OF RESPONSIBILITY", "County residency, intercounty transfers (ICT), and jurisdictional rules", 3),
    "ARTICLE 04": ("ARTICLE 04 - APPLICATION PROCESS", "Intake procedures, verifications, expedited medical need, renewals, and NOAs", 4),
    "ARTICLE 05": ("ARTICLE 05 - Medi-Cal Programs", "MAGI, Non-MAGI, ABD, Foster Care, MSP, Pickle Amendment, and specialized aid programs", 5),
    "ARTICLE 06": ("ARTICLE 06 - Institutional Status", "Public institutions, mental disease facilities, and inmates medical coverage", 6),
    "ARTICLE 07": ("ARTICLE 07 - Citizenship/Immigration Status", "Citizenship verification, PRUCOL, and immigrant eligibility rules", 7),
    "ARTICLE 08": ("ARTICLE 08 - Responsible Relatives & Unit Determination", "Medi-Cal family budget units (MFBU), tax dependency, and spousal allocations", 8),
    "ARTICLE 09": ("ARTICLE 09 - Property", "Real and personal property evaluation, principal residence, and transfers", 9),
    "ARTICLE 10": ("ARTICLE 10 - NON-MAGI INCOME", "Earned/unearned income, deductions, and Non-MAGI budgeting computations", 10),
    "ARTICLE 11": ("ARTICLE 11 - Maintenance Needs", "Maintenance need standards and basic subsistence income levels", 11),
    "ARTICLE 12": ("ARTICLE 12 - Share-of-Cost", "Share of Cost (SOC) determination, liability computation, and form processing", 12),
    "ARTICLE 13": ("ARTICLE 13 - PERIOD OF ELIGIBILITY", "Retroactive coverage, ongoing eligibility periods, and continuous coverage", 13),
    "ARTICLE 14": ("ARTICLE 14 - MEDI-CAL CARD USE AND ISSUANCE", "Benefits Identification Card (BIC) issuance, replacements, and authorization letters", 14),
    "ARTICLE 15": ("ARTICLE 15 - OTHER HEALTH CARE COVERAGE AND MEDICARE BUY-IN COVERAGE", "Other Health Coverage (OHC), third-party liability, and Medicare Part A/B buy-in", 15),
    "ARTICLE 16": ("ARTICLE 16 - OVERPAYMENTS, FRAUD AND IMPROPER UTILIZATION", "Fraud prevention, estate recovery, administrative disqualification, and overpayments", 16),
    "ARTICLE 17": ("ARTICLE 17 - MEDI-CAL SPECIAL TREATMENT PROGRAMS", "Kidney transplant, organ anti-rejection, dialysis, and parenteral nutrition programs", 17),
    "ARTICLE 20": ("ARTICLE 20 - PERFORMANCE STANDARDS", "Casework processing standards, redetermination timelines, and MEDS alerts", 18),
    "ARTICLE 21": ("ARTICLE 21 - MAGI APTC and Health Care Reform", "Modified Adjusted Gross Income (MAGI), Covered CA, tax households, and ACA rules", 19),
    "Special Notices": ("Special Notices & Policy Bulletins", "County Medi-Cal Bulletins, COLA notices, emergency directives, and annual adjustments", 99)
}

def clean_doc_title(raw_title):
    t = raw_title.replace('.doc', '').replace('.pdf', '').replace('_', ' ').strip()
    return re.sub(r'\s+', ' ', t)

def main():
    with open(PART1_PATH) as f:
        part1 = json.load(f)['value']

    with open(PART2_PATH) as f:
        part2 = json.load(f)['value']['part2']

    all_sections = part1 + part2

    with open(DOCS_PATH, 'r', encoding='utf-8') as f:
        docs = json.load(f)

    # Collect indices of Medi-Cal documents
    mc_indices = [i for i, d in enumerate(docs) if 'Medi-Cal' in d.get('programs', [])]
    print(f"Total Medi-Cal docs in DB: {len(mc_indices)}")

    doc_counter = 0
    updated_count = 0

    for sec in all_sections:
        sec_id = sec.get('sectionId', '')
        # normalize sec_id
        match = re.match(r'^(ARTICLE\s*\d+)', sec_id, re.IGNORECASE)
        normalized_key = match.group(1).upper() if match else ("Special Notices" if "Special" in sec_id else sec_id)
        
        # Format key as ARTICLE XX (two digits)
        if normalized_key.startswith("ARTICLE"):
            num = re.search(r'\d+', normalized_key).group(0)
            normalized_key = f"ARTICLE {int(num):02d}"

        if normalized_key not in ARTICLE_DESCRIPTIONS:
            print(f"WARNING: Unknown section key: {normalized_key}")
            continue

        cat_title, cat_desc, order_num = ARTICLE_DESCRIPTIONS[normalized_key]
        cat_id = normalized_key.lower().replace(' ', '-')

        for doc_item in sec['documents']:
            raw_title = doc_item['title']
            cleaned = clean_doc_title(raw_title)

            db_idx = mc_indices[doc_counter]
            d = docs[db_idx]

            # Parse section_num and section_title
            if normalized_key == "Special Notices":
                sn_match = re.match(r'^(SN\s*[\d\-_]+)\s*(.*)$', cleaned, re.IGNORECASE)
                if sn_match:
                    s_num = sn_match.group(1).replace('_', ' ')
                    s_title = sn_match.group(2).strip()
                else:
                    s_num = "SN"
                    s_title = cleaned
            else:
                sec_match = re.match(r'^(Section\s+[0-9A-Za-z]+)\s*[-:]*\s*(.*)$', cleaned, re.IGNORECASE)
                if sec_match:
                    s_num = sec_match.group(1)
                    s_title = sec_match.group(2).strip()
                else:
                    s_num = ""
                    s_title = cleaned

            d["section_num"] = s_num
            d["section_title"] = s_title
            d["chapter"] = cat_title
            d["category"] = cat_title
            d["category_desc"] = cat_desc
            d["category_id"] = cat_id
            d["order"] = order_num

            # Format published date if present in scrape
            if doc_item.get('published'):
                pub = doc_item['published']
                # format MM/DD/YYYY to YYYY-MM-DDT00:00:00Z if possible
                try:
                    parts = pub.split('/')
                    if len(parts) == 3:
                        m, day, y = int(parts[0]), int(parts[1]), int(parts[2])
                        d["published_on"] = f"{y:04d}-{m:02d}-{day:02d}T00:00:00Z"
                except Exception:
                    pass

            doc_counter += 1
            updated_count += 1

    print(f"Successfully updated {updated_count} Medi-Cal documents across {len(all_sections)} sections.")

    with open(DOCS_PATH, 'w', encoding='utf-8') as f:
        json.dump(docs, f, indent=2, ensure_ascii=False)

    print("Saved updated documents.json.")

if __name__ == '__main__':
    main()
