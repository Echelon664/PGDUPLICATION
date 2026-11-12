#!/usr/bin/env python3
import json
import re

DOCS_PATH = "/Users/echelon619/Desktop/ChrisPG/data/documents.json"
CF_JSON_PATH = "/Users/echelon619/Desktop/ChrisPG/data/calfresh_folder_sections.json"

CHAPTER_METADATA = {
    "63-100": ("63-100 Application Process", "Household concept, application filing, expedited service, interviews, and verification", 1),
    "63-150": ("63-150 Non-Financial", "Identity, residency, citizenship, non-citizen status, CFAP, student rules, and work quit", 2),
    "63-200": ("63-200 Resources", "Resource eligibility determination, liquid assets, and excluded resources", 3),
    "63-220": ("63-220 Income", "Earned income, unearned income, income exclusions, and self-employment", 4),
    "63-230": ("63-230 Income Deductions", "Standard deduction, earned income deduction, excess medical, dependent care, and shelter costs", 5),
    "63-240": ("63-240 Households with Special Circumstances", "Substantial lottery or gambling winnings and specialized eligibility", 6),
    "63-250": ("63-250 Budgeting and Benefit Calculation", "Prospective budgeting, reasonably anticipated income, migrant farmworkers, and allotment tables", 7),
    "63-270": ("63-270 Semi-Annual Reporting", "Semi-Annual Reporting (SAR), SAR cycle, and mandatory SAR 7 report processing", 8),
    "63-280": ("63-280 Mid-Period Reporting", "Voluntary and mandatory mid-period changes, IRT reporting, overissuances, and underissuances", 9),
    "63-300": ("63-300 Certification", "Certification periods, household classification, Notices of Action (NOA), and recertification", 10),
    "63-320": ("63-320 Transitional CalFresh", "Transitional CalFresh (TCF) benefits following CalWORKs cash aid discontinuance", 11),
    "63-330": ("63-330 CalFresh Expansion for SSI-SSP Recipients", "SSI/SSP expansion, Supplemental Nutrition Benefit (SNB), and Transitional Nutrition Benefit (TNB)", 12),
    "63-350": ("63-350 Case Management", "Case assignment, confidentiality, client requests, case record inspections, and intercounty transfers", 13),
    "63-360": ("63-360 Elderly Simplified Application Project", "ESAP streamlined certification and 36-month certification periods for elderly/disabled units", 14),
    "63-370": ("63-370 Minimum Nutrition Benefit (MNB) Pilot Program", "Minimum Nutrition Benefit state pilot program guidelines and supplemental allotments", 15),
    "63-380": ("63-380 Prepared Meal Programs", "Authorized restaurant meals, communal dining, and prepared meal purchases for eligible households", 16),
    "63-420": ("63-420 Work Incentive Nutrition Supplement (WINS)", "WINS monthly food supplement for working families receiving CalFresh", 17),
    "63-450": ("63-450 Claims & Adjustments", "Establishment of claims, non-fraud, Intentional Program Violation (IPV), and claim recoupment", 18),
    "63-500": ("63-500 Disaster CalFresh and Household Misfortune", "Disaster CalFresh (D-CalFresh) operations and food replacement for household misfortune", 19),
    "63-600": ("63-600 Questions and Answers", "Official County eligibility clarification questions and administrative answers", 20),
    "63-900": ("63-900 CalFresh Work-Related Policy Areas", "General work registration, CFET employment & training, and ABAWD work requirements", 21),
    "63-1100": ("63-1100 Handbook / Eligibility Tables", "CalFresh eligibility standards tables, income thresholds, and reference definitions", 22),
    "Special Notices": ("Special Notices & Policy Bulletins", "County policy bulletins, COLA adjustments, emergency directives, and annual adjustments", 99)
}

def main():
    with open(CF_JSON_PATH) as f:
        items = json.load(f)

    sec_to_ch = {}

    for it in items[1:]:
        raw_title = it['title']
        if raw_title.startswith('Special Notices') or raw_title.isdigit():
            continue
        m = re.match(r'^(63-\d+)', raw_title)
        if not m:
            continue
        code = m.group(1)
        if code in CHAPTER_METADATA:
            ch_name, ch_desc, order_num = CHAPTER_METADATA[code]
        else:
            ch_name = raw_title
            ch_desc = "Official County Policy and Procedure Sections"
            order_num = 50

        ch_info = {
            "code": code,
            "category": ch_name,
            "category_desc": ch_desc,
            "category_id": "cf-" + code.lower(),
            "order": order_num
        }

        for dt in it.get('docTitles', []):
            m_sec = re.match(r'^(63-\d+)', dt)
            if m_sec:
                sec_to_ch[m_sec.group(1)] = ch_info

    with open(DOCS_PATH, 'r', encoding='utf-8') as f:
        docs = json.load(f)

    cf_count = 0
    updated_count = 0

    for d in docs:
        if 'CalFresh' not in d.get('programs', []):
            continue
        cf_count += 1
        t = d.get('title', '')

        # Check for Special Notices
        if t.startswith('SN ') or 'Special Notice' in t or d.get('chapter') == 'Special Notices':
            sn_m = re.match(r'^(SN\s*[\d\-_]+)\s*(.*)$', t, re.IGNORECASE)
            s_num = sn_m.group(1) if sn_m else "SN"
            s_title = sn_m.group(2).strip() if sn_m else t

            d["section_num"] = s_num
            d["section_title"] = s_title
            d["chapter"] = "Special Notices & Policy Bulletins"
            d["category"] = "Special Notices & Policy Bulletins"
            d["category_desc"] = "County policy bulletins, COLA adjustments, emergency directives, and annual adjustments"
            d["category_id"] = "cf-sn"
            d["order"] = 99
            updated_count += 1
            continue

        # Regular CalFresh document
        m_sec = re.match(r'^(63-\d+)\s*[-:]*\s*(.*)$', t)
        if m_sec:
            sec_code = m_sec.group(1)
            sec_title = m_sec.group(2).strip()
            ch_info = sec_to_ch.get(sec_code)
            if ch_info:
                d["section_num"] = sec_code
                d["section_title"] = sec_title
                d["chapter"] = ch_info["category"]
                d["category"] = ch_info["category"]
                d["category_desc"] = ch_info["category_desc"]
                d["category_id"] = ch_info["category_id"]
                d["order"] = ch_info["order"]
                updated_count += 1
            else:
                print(f"Warning: No chapter mapping for section {sec_code}: {t}")
        else:
            print(f"Warning: Could not parse section code from title: {t}")

    print(f"Total CalFresh docs: {cf_count}")
    print(f"Successfully updated: {updated_count}")

    with open(DOCS_PATH, 'w', encoding='utf-8') as f:
        json.dump(docs, f, indent=2, ensure_ascii=False)

    print("Saved updated documents.json.")

if __name__ == '__main__':
    main()
