#!/usr/bin/env python3
import json, html, os, re

import catalog

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, "templates", "index.html")
DOCS_PATH = os.path.join(BASE_DIR, "data", "documents.json")

full_docs = catalog.load_documents(DOCS_PATH)

print(f"Loaded {len(full_docs)} unique documents.")

cf_count = sum(1 for d in full_docs if 'CalFresh' in d.get('programs', []))
cw_count = sum(1 for d in full_docs if 'CalWORKs' in d.get('programs', []))
mc_count = sum(1 for d in full_docs if 'Medi-Cal' in d.get('programs', []))
all_count = len(full_docs)

# Live index size and the date of the last full County comparison, for the page header.
from indexer import chunk_documents
chunk_count = len(chunk_documents(DOCS_PATH))
verified_html = ""
verified_top = ""
try:
    with open(os.path.join(BASE_DIR, "data", "county_sync", "manifest.json"), "r", encoding="utf-8") as f:
        import datetime
        _verified = datetime.datetime.strptime(json.load(f)["verified_at"], "%Y-%m-%dT%H:%M:%SZ")
        verified_html = (
            '<p class="text-xs text-emerald-700 font-semibold mt-1">'
            f'Every PDF matched the County site on {_verified.strftime("%B %-d, %Y")}. '
            '<a href="/sync" class="underline">See the check</a></p>'
        )
        verified_top = (
            '<a href="/sync" class="hidden sm:inline-flex items-center gap-1.5 hover:text-slate-900" '
            'title="Every PDF matched the County site in the last full check">'
            '<svg class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">'
            '<path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
            f'Matches County site · {_verified.strftime("%b %-d, %Y")}</a>'
        )
except (OSError, ValueError, KeyError):
    pass

print(f"Counts: CalFresh={cf_count}, CalWORKs={cw_count}, Medi-Cal={mc_count}, All={all_count}")

CHAPTER_DESCRIPTIONS = {
    # CalFresh (Folder 542) - 22 Official County Chapters & Special Notices
    '63-100 Application Process': 'Household concept, application filing, expedited service, interviews, and verification',
    '63-150 Non-Financial': 'Identity, residency, citizenship, non-citizen status, CFAP, student rules, and work quit',
    '63-200 Resources': 'Resource eligibility determination, liquid assets, and excluded resources',
    '63-220 Income': 'Earned income, unearned income, income exclusions, and self-employment',
    '63-230 Income Deductions': 'Standard deduction, earned income deduction, excess medical, dependent care, and shelter costs',
    '63-240 Households with Special Circumstances': 'Substantial lottery or gambling winnings and specialized eligibility',
    '63-250 Budgeting and Benefit Calculation': 'Prospective budgeting, reasonably anticipated income, migrant and seasonal farmworkers, income and benefit calculations, and income of ineligible or non-household members',
    '63-270 Semi-Annual Reporting': 'Semi-Annual Reporting (SAR), SAR cycle, and mandatory SAR 7 report processing',
    '63-280 Mid-Period Reporting': 'Voluntary and mandatory mid-period changes, IRT reporting, overissuances, and underissuances',
    '63-300 Certification': 'Certification periods, household classification, Notices of Action (NOA), and recertification',
    '63-320 Transitional CalFresh': 'Transitional CalFresh (TCF) benefits following CalWORKs cash aid discontinuance',
    '63-330 CalFresh Expansion for SSI-SSP Recipients': 'SSI/SSP expansion, Supplemental Nutrition Benefit (SNB), and Transitional Nutrition Benefit (TNB)',
    '63-350 Case Management': 'Case assignment, confidentiality, client requests, case record inspections, and intercounty transfers',
    '63-360 Elderly Simplified Application Project': 'ESAP streamlined certification and 36-month certification periods for elderly/disabled units',
    '63-370 Minimum Nutrition Benefit (MNB) Pilot Program': 'Minimum Nutrition Benefit state pilot program guidelines and supplemental allotments',
    '63-380 Prepared Meal Programs': 'Using CalFresh for home-delivered meals, communal dining facilities, and authorized homeless meal providers',
    '63-420 Work Incentive Nutrition Supplement (WINS)': 'WINS monthly food supplement for working families receiving CalFresh',
    '63-450 Claims & Adjustments': 'Establishment of claims, non-fraud, Intentional Program Violation (IPV), and claim recoupment',
    '63-500 Disaster CalFresh and Household Misfortune': 'Disaster CalFresh (D-CalFresh) operations and food replacement for household misfortune',
    '63-600 Questions and Answers': 'Official County eligibility clarification questions and administrative answers',
    '63-900 CalFresh Work-Related Policy Areas': 'General work registration, CFET employment & training, and ABAWD work requirements',
    '63-1100 Handbook / Eligibility Tables': 'CalFresh eligibility standards tables, income thresholds, and reference definitions',
    'Special Notices & Policy Bulletins': 'County Policy Bulletins, COLA notices, emergency directives, and annual adjustments',

    # CalWORKs (Folder 448) - 44 Official County Chapters & Special Notices
    '10-001 Background': 'CalWORKs and Employment Services legal authority, program goals, and administrative framework',
    '10-002 Federal Work Participation Rate (WPR)': 'Federal Work Participation Rate requirements, data reporting, and verification standards',
    '10-005 Welfare-to-Work': 'Welfare-to-Work flow, orientation, appraisal, assessment, employment plans, and teen participation',
    '10-006 Learning Disabilities': 'Learning disability screening, evaluation protocols, and workplace accommodations',
    '10-007 Family Stabilization': 'Intensive case management, barrier removal, and family stabilization support services',
    '10-008 CalWORKs Housing Support Program': 'Housing identification, rent assistance, rapid re-housing, and housing case management',
    '10-009 Home Visiting Program': 'Voluntary home visits by a nurse or other trained professional for pregnant people and parents of young children',
    '10-010 Child Care': 'Stage One child care eligibility, provider authorization, payment rules, and NOA requirements',
    '10-011 Supportive Services': 'Transportation reimbursement, work-related expenses, tools/uniforms, and mental health/substance abuse support',
    '10-020 Exemptions & Good Cause': 'Welfare-to-Work participation exemptions and good cause criteria',
    '10-025 Compliance Process': 'Employment Services noncompliance, cause determinations, compliance plans, and sanctions',
    '10-030 Participants Rights': 'Participant rights, formal grievance procedures, and state fair hearing rules',
    '10-050 Community Service': 'Community service work experience placements, activities, and hour requirements',
    '10-150 Subsidized Employment Programs': 'Expanded Subsidized Employment (ESE) and work experience wage subsidy programs',
    '10-160 Wrap Around': 'Comprehensive wraparound family services and multi-agency support',
    '10-170 CalWORKs Outcomes and Accountability Review (Cal-OAR)': 'State performance measures, continuous quality improvement (CQI), and outcome metrics',
    '10-200 Refugee Services': 'Refugee employment services, coordination with resettlement agencies, and language access',
    '10-260 Document Capture Procedures for Employment Services Contractors': 'Electronic document imaging standards, contractor workflows, and indexing protocols',
    '10-300 WTW Activity Documentation and Reporting Requirements': 'Work activity logs, attendance verification, timesheets, and reporting protocols',
    '15-000 Cal-Learn': 'Mandatory program for pregnant and parenting teens, school attendance, and bonuses/sanctions',
    '15-100 TIME ON AID': '60-month cumulative lifetime cash aid time limit, tracking, and good cause exemptions',
    '19-000 Confidentiality of Information & Records': 'Case confidentiality, safeguarding public assistance records, and release authorizations',
    '20-000 Integrity': 'Early fraud prevention, Special Investigations Unit (SIU), and child care program integrity',
    '22-000 Notifications': 'Adequate and timely Notice of Action (NOA) standards and verification requests',
    '40-100 Application and Redetermination': 'Applications, Immediate Need, Social Security Numbers, Diversion, family violence, continuing benefits, redeterminations, and intercounty transfers',
    '40-125 Restoration of Aid': 'Expedited restoration of aid following discontinuance within 12 months',
    '40-183 CalWORKs Special Programs': 'Approved Relative Caregiver (ARC), extended CalWORKs for non-minor dependents (NMD), and family reunification',
    '41-400 Deprivation': 'Parental deprivation factors: unemployment (U-parent), absence, physical/mental incapacity, or death',
    '41-500 Assistance Unit': 'Assistance unit (AU) composition, mandatory inclusion rules, caretaker relatives, and temporary absence',
    '42-100 Age-Immunization-School Attendance': 'Age limits, school attendance mandates for children under 16, and preschool immunization requirements',
    '42-200 Property': 'Property limits, real and personal property, items included and excluded, net market value, restricted accounts, the home exclusion, and motor vehicles',
    '42-400 Residence': 'State residency, county jurisdiction, citizenship verification, and qualified immigrant eligibility',
    '43-100 Responsible Relatives': 'Legal responsibility of parents and financial contributions of unrelated adults in the home',
    '43-200 Child Support': 'Child support assignment of rights, cooperation with Department of Child Support Services (DCSS), and good cause',
    '44-100 Income': 'Earned and unearned income, $450/month disregard, 50% earned income disregard, and exempt income',
    '44-200 Special Needs': 'Recurring and nonrecurring special needs, pregnancy dietary supplements, and homeless assistance (temp/perm)',
    '44-260 Annual Reporting (Child Only Cases)': 'Annual reporting and budgeting rules for child-only assistance units',
    '44-270 Semi-Annual Reporting (SAR)': 'Semi-Annual Reporting (SAR 7) cycles, Income Reporting Threshold (IRT), and mandatory mid-period reports',
    '44-300 Benefit Payments': 'Region 1 Maximum Aid Payment (MAP) calculations, proration, vendor payments, and issuance dates',
    '44-350 Overpayment-IPV-Underpayment': 'Overpayment investigations, IPV sanctions, 10% grant reduction recoupment, and corrective underpayments',
    '45-000 CalWORKs Questions and Answers': 'County policy clarifications, state interpretations, and questions & answers',
    '45-200 Resources and Desk Aids': 'Assistance standards charts, MAP levels, property tables, SAR cycles, and income desk aids',
    '69-205 Refugee Cash Assistance (RCA)': 'Federal RCA program eligibility, time limits, and budgeting',
    '70-100 Trafficking and Crime Victims Assistance Program (TCVAP)': 'State-funded cash and supportive services for eligible victims of crime',
    'Special Notices & Policy Bulletins': 'County Policy Bulletins, COLA notices, emergency directives, and annual adjustments',

    # Medi-Cal Articles
    'ARTICLE 01 - DEFINITIONS': 'Official Medi-Cal terms, beneficiary definitions, and program concepts',
    'ARTICLE 02 - CONFIDENTIALITY': 'Safeguarding Medi-Cal case records and confidential health information',
    'ARTICLE 03 - COUNTY OF RESPONSIBILITY': 'County residency, intercounty transfers (ICT), and jurisdictional rules',
    'ARTICLE 04 - APPLICATION PROCESS': 'Intake procedures, verifications, expedited medical need, renewals, and NOAs',
    'ARTICLE 05 - Medi-Cal Programs': 'MAGI, Non-MAGI, ABD, Foster Care, MSP, Pickle Amendment, and specialized aid programs',
    'ARTICLE 06 - Institutional Status': 'Public institutions, mental disease facilities, and inmates medical coverage',
    'ARTICLE 07 - Citizenship/Immigration Status': 'Citizenship verification, PRUCOL, and immigrant eligibility rules',
    'ARTICLE 08 - Responsible Relatives & Unit Determination': 'Medi-Cal Family Budget Units, responsible relatives, tax dependency, long-term care and PACE, caretaker relatives, domestic partners, and same-sex marriages',
    'ARTICLE 09 - Property': 'Real and personal property evaluation, principal residence, and transfers',
    'ARTICLE 10 - NON-MAGI INCOME': 'Earned/unearned income, deductions, and Non-MAGI budgeting computations',
    'ARTICLE 11 - Maintenance Needs': 'Maintenance need standards and basic subsistence income levels',
    'ARTICLE 12 - Share-of-Cost': 'Share of Cost (SOC) determination, liability computation, and form processing',
    'ARTICLE 13 - PERIOD OF ELIGIBILITY': 'Beginning date, period and final date of eligibility, and retroactive coverage',
    'ARTICLE 14 - MEDI-CAL CARD USE AND ISSUANCE': 'Benefits Identification Card (BIC) issuance, replacements, and authorization letters',
    'ARTICLE 15 - OTHER HEALTH CARE COVERAGE AND MEDICARE BUY-IN COVERAGE': 'Other Health Coverage, third party liability claims, Medicare, and Medicare Part B Buy-In',
    'ARTICLE 16 - OVERPAYMENTS, FRAUD AND IMPROPER UTILIZATION': 'Fraud prevention and referrals, overpayments, estate recovery, employee conflicts of interest, and altered documents',
    'ARTICLE 17 - MEDI-CAL SPECIAL TREATMENT PROGRAMS': 'Special treatment coverage for kidney dialysis and total parenteral nutrition, and anti-rejection medications after an organ transplant',
    'ARTICLE 20 - PERFORMANCE STANDARDS': 'Casework processing standards, redetermination timelines, and MEDS alerts',
    'ARTICLE 21 - MAGI APTC and Health Care Reform': 'Modified Adjusted Gross Income (MAGI), Covered CA, tax households, and ACA rules',
    'Special Notices & Policy Bulletins': 'County special notices: COLA updates, emergency directives, and annual adjustments'
}

def categorize_doc(doc):
    title = doc.get('title', '')
    chapter = doc.get('chapter', '')
    programs = doc.get('programs', [])
    t = f"{title} {chapter}".lower()
    
    if 'CalFresh' in programs:
        cat = doc.get('category')
        if cat:
            order = doc.get('order', 50)
            cat_id = doc.get('category_id') or ('cf-' + cat.replace(' ', '-').lower())
            return cat, cat_id, order
        if 'sn ' in t or 'special notice' in t:
            return 'Special Notices & Policy Bulletins', 'cf-sn', 99
        return '63-100 Application Process', 'cf-63-100', 1

    elif 'CalWORKs' in programs:
        cat = doc.get('category')
        if cat:
            order = doc.get('order', 50)
            sec_num = doc.get('section_num', '')
            cat_id = 'cw-' + sec_num.replace(' ', '-').lower() if sec_num else 'cw-sec'
            return cat, cat_id, order
        if 'sn ' in t or 'notice' in t:
            return 'Special Notices & Policy Bulletins', 'cw-sn', 99
        return '40-100 Application and Redetermination', 'cw-40-100', 25

    else: # Medi-Cal
        cat = doc.get('category')
        if cat:
            order = doc.get('order', 50)
            cat_id = doc.get('category_id') or ('mc-' + cat.replace(' ', '-').lower())
            return cat, cat_id, order
        if 'sn ' in t or 'acwdl' in t or 'bulletin' in t or 'special notice' in t:
            return 'Special Notices & Policy Bulletins', 'mc-sn', 99
        return 'ARTICLE 04 - APPLICATION PROCESS', 'mc-art-04', 4

embedded_docs = []
for d in full_docs:
    cat_name, cat_id, cat_order = categorize_doc(d)
    content_snippet = d.get('content', '')[:2500].strip()
    cat_desc = CHAPTER_DESCRIPTIONS.get(cat_name, d.get('category_desc', 'Official County Policy and Procedure Sections'))
    embedded_docs.append({
        "id": d.get("id"),
        "title": d.get("title", ""),
        "chapter": d.get("chapter", ""),
        "programs": d.get("programs", []),
        "section_num": d.get("section_num", ""),
        "section_title": d.get("section_title", ""),
        "category": cat_name,
        "category_id": cat_id,
        "category_desc": cat_desc,
        "order": cat_order,
        "published_on": d.get("published_on", ""),
        "file_type": d.get("file_type", "PDF"),
        "local_pdf_url": d.get("local_pdf_url", ""),
        "official_url": d.get("official_url", ""),
        "summary": d.get("summary", ""),
        "summary_status": d.get("summary_status", ""),
        "source_missing": bool(d.get("source_missing")),
        "pdf_date": d.get("pdf_date", ""),
        "pdf_date_label": d.get("pdf_date_label", ""),
        "content_text": content_snippet
    })

embedded_json_str = json.dumps(embedded_docs)

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Policy Search Engine</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible+Next:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <script>
    // Apply the saved theme (or the device setting) before the page paints.
    (function () {{
      let saved = null;
      try {{ saved = localStorage.getItem('theme'); }} catch (e) {{}}
      const dark = saved ? saved === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.classList.toggle('dark', dark);
    }})();
  </script>
  <script src="https://cdn.tailwindcss.com/3.4.17"></script>
  <style>
    /* Atkinson Hyperlegible Next is designed for legibility on screens. The
       17px root scales every rem-based Tailwind size up from the 16px default. */
    html {{
      font-size: 17px;
    }}
    html, body, button, input, select, textarea {{
      font-family: 'Atkinson Hyperlegible Next', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
    }}
    .gradient-header {{
      background: #0b2545;
    }}
    ::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    ::-webkit-scrollbar-track {{
      background: rgba(0, 0, 0, 0.05);
    }}
    ::-webkit-scrollbar-thumb {{
      background: rgba(100, 116, 139, 0.4);
      border-radius: 3px;
    }}
    .chapter-chevron {{
      transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    input[type="search"]::-webkit-search-cancel-button,
    input[type="search"]::-webkit-search-decoration {{
      -webkit-appearance: none;
      appearance: none;
    }}
    .search-seg {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }}
    .search-seg-btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      min-height: 48px;
      padding: 0 18px;
      border: 1px solid #cbd5e1;
      border-radius: 12px;
      background: #fff;
      color: #334155;
      font-size: 15px;
      font-weight: 700;
      white-space: nowrap;
      cursor: pointer;
      transition: background 0.15s, color 0.15s, border-color 0.15s;
    }}
    .search-seg-btn:hover {{
      background: #f1f5f9;
      border-color: #94a3b8;
    }}
    .search-seg-btn.is-active {{
      background: #2563eb;
      border-color: #2563eb;
      color: #fff;
    }}
    .search-seg-btn.is-active:hover {{
      background: #1d4ed8;
      border-color: #1d4ed8;
    }}
    .search-seg-btn:disabled {{
      opacity: 0.6;
      cursor: not-allowed;
    }}
    .site-mark {{
      width: 32px; height: 32px; flex: none; border-radius: 9px;
      display: inline-flex; align-items: center; justify-content: center;
      background: #dbeafe; color: #1d4ed8;
    }}
    .guides-menu {{ position: relative; }}
    .guides-menu > summary {{ list-style: none; }}
    .guides-menu > summary::-webkit-details-marker {{ display: none; }}
    .guides-list {{
      position: absolute; right: 0; top: calc(100% + 8px); z-index: 30; min-width: 280px;
      display: flex; flex-direction: column; padding: 6px;
      background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
    }}
    .guides-list a {{ white-space: nowrap; padding: 8px 10px; border-radius: 6px; color: #1e293b; font-size: 14px; text-decoration: none; }}
    .guides-list a:hover {{ background: #f1f5f9; }}
    .prog-seg {{
      display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 4px; padding: 4px;
      background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 14px;
    }}
    .program-btn {{
      display: flex; align-items: center; justify-content: center; gap: 8px; min-height: 42px; padding: 0 8px;
      border: 0; border-radius: 10px; background: transparent; color: #475569;
      font-size: 15px; font-weight: 600; cursor: pointer; transition: background 0.15s, color 0.15s, box-shadow 0.15s;
    }}
    .program-btn:hover {{ background: #e2e8f0; color: #0f172a; }}
    .program-btn.is-active {{ background: #fff; color: #0f172a; font-weight: 800; box-shadow: 0 0 0 1px #cbd5e1, 0 1px 2px rgba(15, 23, 42, 0.08); }}
    .program-btn:focus-visible, .search-seg-btn:focus-visible, .guides-menu > summary:focus-visible {{ outline: 2px solid #2563eb; outline-offset: 2px; }}
    .theme-toggle {{
      display: inline-flex; align-items: center; gap: 6px; min-height: 34px; padding: 0 10px;
      border: 1px solid #cbd5e1; border-radius: 999px; background: transparent; color: #334155;
      font-size: 13px; font-weight: 600; cursor: pointer; white-space: nowrap;
    }}
    .theme-toggle:hover {{ background: #f1f5f9; }}
    .theme-toggle:focus-visible {{ outline: 2px solid #2563eb; outline-offset: 2px; }}
    .theme-icon-sun {{ display: none; }}
    html.dark .theme-icon-sun {{ display: inline; }}
    html.dark .theme-icon-moon {{ display: none; }}
    .prog-dot {{ width: 9px; height: 9px; border-radius: 50%; flex: none; }}
    .prog-count {{ font-size: 13px; font-weight: 600; color: #64748b; }}
    @media (max-width: 520px) {{
      .prog-seg {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    .search-scope {{
      flex: none;
      display: inline-flex;
      align-items: center;
      padding: 3px 8px;
      border-radius: 999px;
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      color: #1d4ed8;
      font-size: 12.5px;
      font-weight: 800;
      white-space: nowrap;
    }}
    @media (max-width: 400px) {{
      .search-scope {{ display: none; }}
    }}
__CHAPTER_NAV_CSS__
__THEME_CSS__
  </style>
</head>
<body class="bg-[#0b2545] text-slate-900 antialiased p-3 sm:p-5 min-h-screen">

  <div class="max-w-5xl mx-auto bg-[#0b2545] text-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-clip flex flex-col">
    
    <!-- Top bar: name, County check, County guide links -->
    <header class="site-top bg-white border-b border-slate-200 px-4 sm:px-5 py-2.5 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
      <div class="flex items-center gap-2.5 min-w-0">
        <span class="site-mark" aria-hidden="true">
          <svg class="w-[18px] h-[18px]" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.25v13m0-13C10.83 5.48 9.25 5 7.5 5S4.17 5.48 3 6.25v13C4.17 18.48 5.75 18 7.5 18s3.33.48 4.5 1.25m0-13C13.17 5.48 14.75 5 16.5 5s3.33.48 4.5 1.25v13C19.83 18.48 18.25 18 16.5 18s-3.33.48-4.5 1.25"/></svg>
        </span>
        <div class="leading-tight min-w-0">
          <div class="text-[15px] font-bold text-slate-900">Policy Search Engine</div>
          <div class="text-xs text-slate-500">HHSA SDCounty PG</div>
        </div>
      </div>
      <div class="flex items-center gap-4 text-[13px] text-slate-600">
        {verified_top}
        <button type="button" id="themeToggle" class="theme-toggle" onclick="toggleTheme()" aria-pressed="false" title="Switch to dark mode">
          <svg class="theme-icon-moon w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>
          <svg class="theme-icon-sun w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path stroke-linecap="round" d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41m11.32-11.32l1.41-1.41"/></svg>
          <span class="theme-label">Dark mode</span>
        </button>
        <details class="guides-menu">
          <summary class="inline-flex items-center gap-1 cursor-pointer select-none hover:text-slate-900">County guides
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M6 9l6 6 6-6"/></svg>
          </summary>
          <div class="guides-list">
            <a href="https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=542" target="_blank" rel="noopener">CalFresh guide on the County site ↗</a>
            <a href="https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=448" target="_blank" rel="noopener">CalWORKs guide on the County site ↗</a>
            <a href="https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=599" target="_blank" rel="noopener">Medi-Cal guide on the County site ↗</a>
            <a href="/sync">County source check</a>
          </div>
        </details>
      </div>
    </header>

    <!-- Title, program tabs and search -->
    <div class="site-hero bg-white px-4 sm:px-6 pt-6 sm:pt-8 pb-5 border-b border-slate-200">
      <div class="max-w-3xl mx-auto">
        <h1 class="text-2xl sm:text-[28px] font-extrabold tracking-tight text-slate-900 text-center">Find a policy</h1>
        <p class="text-sm sm:text-[15px] text-slate-600 text-center mt-1 mb-5">
          Search {all_count} CalFresh, CalWORKs and Medi-Cal sections, or pick a program to browse its chapters.
        </p>

        <!-- Program tabs (styled by switchProgram) -->
        <div class="prog-seg" role="group" aria-label="Program">
          <button type="button" id="tab-All" onclick="switchProgram('All')" class="program-btn" title="All programs">
            <span class="prog-dot" style="background:#64748b"></span><span>All</span><span class="prog-count">{all_count}</span>
          </button>
          <button type="button" id="tab-CalFresh" onclick="switchProgram('CalFresh')" class="program-btn is-active" aria-pressed="true" title="CalFresh (SNAP)">
            <span class="prog-dot" style="background:#047857"></span><span>CalFresh</span><span class="prog-count">{cf_count}</span>
          </button>
          <button type="button" id="tab-CalWORKs" onclick="switchProgram('CalWORKs')" class="program-btn" title="CalWORKs (TANF)">
            <span class="prog-dot" style="background:#7e22ce"></span><span>CalWORKs</span><span class="prog-count">{cw_count}</span>
          </button>
          <button type="button" id="tab-Medi-Cal" onclick="switchProgram('Medi-Cal')" class="program-btn" title="Medi-Cal (Medicaid)">
            <span class="prog-dot" style="background:#0f766e"></span><span>Medi-Cal</span><span class="prog-count">{mc_count}</span>
          </button>
        </div>

        <!-- Search box and Search / Ask AI buttons -->
        <form id="searchForm" role="search" onsubmit="handleSearchSubmit(event)" class="flex flex-col sm:flex-row gap-2 mt-3">
          <label for="searchInput" class="sr-only">Search policy manuals</label>
          <div class="flex items-center gap-2 flex-1 min-w-0 min-h-[48px] pl-3.5 pr-1 bg-white border border-slate-300 rounded-xl transition focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/40">
            <svg class="w-[18px] h-[18px] text-slate-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
            <span id="searchScopeChip" class="search-scope">CalFresh</span>
            <input type="search" id="searchInput"
              placeholder="Search CalFresh policy: student eligibility, SUA, SAR 7..."
              aria-describedby="searchScope" aria-controls="searchResultsPageView"
              enterkeyhint="search" autocomplete="off" autocapitalize="off" spellcheck="false"
              class="flex-1 min-w-0 h-12 bg-transparent border-0 outline-none text-slate-900 placeholder:text-slate-500 text-base font-medium">
            <button type="button" id="clearSearchBtn" onclick="clearSearch()" class="hidden shrink-0 h-11 w-11 items-center justify-center rounded-md text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition cursor-pointer" aria-label="Clear search" title="Clear search">
              <span aria-hidden="true">✕</span>
            </button>
          </div>
          <div class="search-seg w-full sm:w-auto shrink-0" role="group" aria-label="Search mode">
            <button type="submit" name="searchMode" value="search" class="search-seg-btn is-active flex-1 sm:flex-none">
              <span data-label>Search</span>
            </button>
            <button type="submit" name="searchMode" value="ask" class="search-seg-btn flex-1 sm:flex-none">
              <svg class="w-3.5 h-3.5 text-amber-500" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.477.859h4z"></path>
              </svg>
              <span data-label>Ask AI</span>
            </button>
          </div>
        </form>
        <p id="searchScope" class="sr-only">Searching the CalFresh (SNAP) guide.</p>
        <p id="searchError" class="hidden text-xs font-semibold text-amber-800 mt-2 px-1" role="alert"></p>

        <p class="text-xs text-slate-500 text-center leading-relaxed mt-3">
          A search tool for County policy guides, not legal advice or a casework decision. To apply or report changes, use
          <a href="https://benefitscal.com/" target="_blank" rel="noopener" class="underline hover:text-slate-800">BenefitsCal.com</a>
          or the <a href="https://www.sandiegocounty.gov/hhsa/" target="_blank" rel="noopener" class="underline hover:text-slate-800">County HHSA site</a>.
        </p>
      </div>
    </div>

    <!-- Main Content Body -->
    <div class="bg-white p-4 sm:p-6 flex-1 flex flex-col gap-5">
      
      <!-- VIEW 1: Manual Chapter & Section Dropdowns View (Default View) -->
      <div id="manualDropdownsView" class="flex flex-col gap-5">
        <!-- Section Catalog Header with Expand / Collapse All Controls -->
        <div class="flex flex-wrap items-center justify-between border-b border-slate-200 pb-3 gap-2">
          <div>
            <h3 id="listHeading" class="font-extrabold text-slate-800 text-sm sm:text-base">
              CalFresh Policy Manual Sections &amp; Chapters ({cf_count})
            </h3>
            <p id="resultMeta" class="text-xs text-slate-500 mt-0.5">
              Pick a chapter, then a document to see its date, summary and PDF.
            </p>
            {verified_html}
          </div>
        </div>

        <!-- List of Documents Grouped by Chapter Dropdowns -->
        <div id="documentsList" class="cn-layout">
          <!-- Populated dynamically when in dropdowns mode -->
        </div>
      </div>

      <!-- VIEW 2: Dedicated Search Results Page View (Opens when searching) -->
      <div id="searchResultsPageView" class="hidden flex flex-col gap-5">
        
        <!-- Search Results Top Navigation Bar with Cancel / Back Button -->
        <div class="bg-gradient-to-r from-blue-50/90 via-slate-50 to-indigo-50/80 border border-blue-200/90 rounded-2xl p-4 sm:p-5 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div class="flex items-start sm:items-center gap-3 min-w-0">
            <!-- Prominent Cancel / Back to Dropdowns Button -->
            <button type="button" onclick="cancelSearchToDropdowns()" class="bg-white hover:bg-slate-100 text-slate-800 border-2 border-slate-300 hover:border-slate-400 font-bold text-xs sm:text-sm px-3.5 py-2.5 rounded-xl transition flex items-center gap-2 shadow-xs cursor-pointer shrink-0" title="Exit search and return to the chapter dropdowns">
              <svg class="w-4 h-4 text-slate-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
              <span>← Back to Dropdowns</span>
            </button>
            
            <div class="min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span id="searchResultScopeBadge" class="bg-blue-600 text-white text-[12px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider shrink-0">CalFresh</span>
                <h3 id="searchResultsHeading" tabindex="-1" class="font-extrabold text-slate-900 text-sm sm:text-base truncate focus:outline-none">
                  Search Results for: <span id="searchResultQueryText" class="text-blue-700">"..."</span>
                </h3>
              </div>
              <p id="searchResultCountText" class="text-xs text-slate-600 mt-0.5" aria-live="polite" aria-atomic="true">
                Searching 100% of internal PDF text with BM25 engine...
              </p>
              <p id="searchCorrection" class="hidden text-sm text-slate-800 mt-1"></p>
            </div>
          </div>

          <!-- Action on the Right: Cancel search button -->
          <div class="flex items-center gap-2 shrink-0 self-end sm:self-auto">
            <button type="button" onclick="cancelSearchToDropdowns()" class="text-xs bg-red-50 hover:bg-red-100 text-red-700 hover:text-red-800 font-bold px-3 py-2 rounded-xl border border-red-200 transition flex items-center gap-1.5 cursor-pointer shadow-2xs">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
              <span>Cancel Search</span>
            </button>
          </div>
        </div>

        <!-- AI Direct Answer Container (Shown on search page if Ask Policy AI used) -->
        <div id="aiAnswerContainer" class="hidden">
          <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-5 shadow-sm">
            <div class="flex items-center justify-between mb-3 border-b border-blue-200/60 pb-2">
              <div class="flex items-center gap-2 text-blue-900 font-bold text-sm">
                <svg class="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z"></path>
                </svg>
                <span>AI Policy Direct Answer</span>
                <span id="aiScopeTag" class="text-xs px-2 py-0.5 rounded-full font-semibold bg-blue-200 text-blue-900 ml-1">CalFresh</span>
              </div>
              <span class="text-xs text-blue-600 font-semibold bg-white/80 px-2.5 py-0.5 rounded border border-blue-200">
                Grounded in Official Manuals
              </span>
            </div>
            <div id="aiAnswerText" class="text-xs sm:text-sm text-slate-800 leading-relaxed space-y-2 mb-4"></div>
            
            <!-- Cited Sources for AI Answer -->
            <div class="border-t border-blue-200 pt-3">
              <h4 class="text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">Cited County Policy References</h4>
              <div id="aiSourcesList" class="grid grid-cols-1 md:grid-cols-2 gap-2"></div>
            </div>
          </div>
        </div>

        <!-- Search Results Document Cards List -->
        <div id="searchResultsList" class="flex flex-col gap-3.5">
          <!-- Populated dynamically when in search mode -->
        </div>

        <!-- Bottom Return to Dropdowns Banner -->
        <div class="pt-4 border-t border-slate-200 flex flex-wrap items-center justify-between gap-3">
          <button type="button" onclick="cancelSearchToDropdowns()" class="bg-slate-800 hover:bg-slate-900 text-white font-bold text-xs sm:text-sm px-4 py-2.5 rounded-xl transition flex items-center gap-2 shadow-sm cursor-pointer">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
            <span>Cancel &amp; Return to Chapter Dropdowns</span>
          </button>
          <span class="text-xs text-slate-400">Tip: You can also press Esc or clear the search bar to return to dropdowns</span>
        </div>

      </div>

    </div>


  </div>

  <!-- In-Page PDF Viewer Modal Overlay -->
  <div id="pdfViewerModal" class="fixed inset-0 z-50 hidden items-center justify-center bg-slate-950/80 backdrop-blur-xs p-2 sm:p-4 md:p-6 transition-all duration-200">
    <div class="relative flex flex-col w-full h-[95vh] max-w-7xl mx-auto bg-white rounded-2xl shadow-2xl overflow-hidden border border-slate-700/30">
      
      <!-- Top Modal Header Bar -->
      <div class="bg-slate-900 text-white px-4 py-3 flex items-center justify-between gap-3 shrink-0 shadow-md">
        <div class="flex items-center gap-2.5 min-w-0">
          <div class="p-1.5 bg-red-600 rounded-lg text-white shrink-0">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"></path></svg>
          </div>
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <span id="pdfModalProgramBadge" class="text-[12px] uppercase tracking-wider font-extrabold px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-400/30 shrink-0">CalFresh</span>
              <h3 id="pdfModalTitle" class="text-xs sm:text-sm font-bold text-slate-100 truncate">Policy Document Title</h3>
            </div>
            <div id="pdfModalMeta" class="text-[13px] text-slate-400 truncate mt-0.5">Section • Official Document</div>
          </div>
        </div>

        <!-- Controls: Toggle Summary, Open in New Tab, Download, Close -->
        <div class="flex items-center gap-1.5 sm:gap-2 shrink-0">
          <button type="button" id="pdfModalSummaryBtn" aria-expanded="false" aria-controls="pdfModalSummaryBar" onclick="toggleModalSummary()" class="bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white px-2.5 py-1.5 rounded-lg text-xs font-semibold transition border border-slate-700 flex items-center gap-1 cursor-pointer" title="Toggle Quick Summary visibility">
            <svg class="w-3.5 h-3.5 text-blue-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path></svg>
            <span class="hidden md:inline">Summary</span>
          </button>
          <a id="pdfModalNewTabBtn" href="#" target="_blank" class="bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-semibold transition border border-slate-700 flex items-center gap-1" title="Open PDF in a new dedicated browser tab">
            <span class="hidden sm:inline">New Tab</span>
            <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
          </a>
          <a id="pdfModalDownloadBtn" href="#" download class="bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-semibold transition border border-slate-700 hidden lg:flex items-center gap-1" title="Download official PDF copy">
            <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
            <span>Download</span>
          </a>
          <button type="button" onclick="closePdfModal()" class="bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1 shadow-sm cursor-pointer ml-1" title="Close PDF Viewer (Esc)">
            <span>Close</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
          </button>
        </div>
      </div>

      <!-- Quick Summary Sub-bar (Dismissible) -->
      <div id="pdfModalSummaryBar" class="hidden bg-blue-50/95 border-b border-blue-200 px-4 py-3 text-xs sm:text-sm text-slate-800 flex items-start justify-between gap-3 shrink-0">
        <div class="flex items-start gap-2 min-w-0">
          <span class="font-bold text-blue-900 shrink-0 text-xs mt-0.5 flex items-center gap-1">
            <svg class="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path></svg>
            Quick Summary:
          </span>
          <span id="pdfModalSummaryText" class="text-slate-700 line-clamp-4 leading-relaxed text-xs sm:text-[15px]">Official policy summary...</span>
        </div>
        <button type="button" onclick="toggleModalSummary()" class="text-slate-400 hover:text-slate-600 p-0.5 rounded cursor-pointer shrink-0" title="Hide Summary Bar">
          ✕
        </button>
      </div>

      <!-- PDF Viewer Body (iframe) -->
      <div class="relative flex-1 bg-slate-100 w-full h-full overflow-hidden">
        <!-- Loading spinner -->
        <div id="pdfModalLoading" class="absolute inset-0 flex flex-col items-center justify-center bg-slate-100/90 backdrop-blur-2xs z-10 text-slate-500">
          <div class="w-9 h-9 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mb-3"></div>
          <span class="text-xs font-semibold text-slate-700">Loading Official County PDF Document...</span>
          <span class="text-[13px] text-slate-400 mt-1">Rendered via Browser Native PDF Viewer</span>
        </div>
        
        <iframe id="pdfViewerFrame" src="" class="w-full h-full border-0" onload="document.getElementById('pdfModalLoading').classList.add('hidden')" title="PDF Viewer"></iframe>
      </div>

    </div>
  </div>

  <script>
    // Essential HTML Escaping Function Defined at Top
    function escapeHtml(str) {{
      if (str === null || str === undefined) return '';
      return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }}

    function getSearchQuery() {{
      const el = document.getElementById('searchInput');
      return (el && el.value) ? el.value.trim() : '';
    }}

    function setSearchQuery(val) {{
      const el = document.getElementById('searchInput');
      if (el) el.value = val;
      updateClearButtonVisibility();
    }}

    function updateClearButtonVisibility() {{
      const input = document.getElementById('searchInput');
      const btn = document.getElementById('clearSearchBtn');
      if (!btn) return;
      const hasText = !!(input && input.value.length > 0);
      btn.classList.toggle('hidden', !hasText);
      btn.classList.toggle('flex', hasText);
    }}

    function showSearchError(message) {{
      const err = document.getElementById('searchError');
      if (!err) return;
      err.textContent = message;
      err.classList.remove('hidden');
    }}

    function hideSearchError() {{
      const err = document.getElementById('searchError');
      if (err) err.classList.add('hidden');
    }}

    function readSearchStateFromUrl() {{
      const params = new URLSearchParams(window.location.search);
      const programParam = params.get('program');
      return {{
        query: (params.get('q') || '').trim(),
        program: PROGRAM_METADATA[programParam] ? programParam : 'CalFresh',
        mode: params.get('mode') === 'ask' ? 'ask' : 'search'
      }};
    }}

    function updateSearchUrl(query, mode, opts = {{}}) {{
      const params = new URLSearchParams(window.location.search);
      if (query) {{
        params.set('q', query);
        params.set('program', activeProgram);
        params.set('mode', mode === 'ask' ? 'ask' : 'search');
      }} else {{
        params.delete('q');
        params.delete('mode');
        if (activeProgram === 'CalFresh') params.delete('program');
        else params.set('program', activeProgram);
      }}
      const qs = params.toString();
      const url = window.location.pathname + (qs ? '?' + qs : '') + window.location.hash;
      const state = {{ query, program: activeProgram, mode }};
      if (opts.replace) window.history.replaceState(state, '', url);
      else window.history.pushState(state, '', url);
    }}

    // Embedded catalog containing all deduplicated documents
    const EMBEDDED_DOCS = {embedded_json_str};
    const DOCS_BY_ID = {{}};
    EMBEDDED_DOCS.forEach(d => {{ DOCS_BY_ID[d.id] = d; }});

    let activeProgram = 'CalFresh';
    const LOCAL_SERVER_BASE = '__SERVER_BASE__';

    const PROGRAM_METADATA = {{
      'CalFresh': {{
        title: 'CalFresh (SNAP)',
        folder: 'Folder 542 (Chapter 63)',
        total: {cf_count},
        color: 'blue',
        placeholder: 'Search CalFresh policy: student eligibility, SUA, SAR 7...',
        chips: [
          {{ label: 'Student Exemption (20-hr)', query: 'student eligibility 20 hours' }},
          {{ label: 'Standard Utility Allowance (SUA)', query: 'Standard Utility Allowance SUA' }},
          {{ label: 'SAR 7 & IRT Thresholds', query: 'Semi Annual Reporting SAR 7 IRT' }},
          {{ label: '3-Day Expedited Service', query: 'Expedited service 3 days criteria' }}
        ]
      }},
      'CalWORKs': {{
        title: 'CalWORKs (TANF)',
        folder: 'Folder 448 (Chapters 40-44)',
        total: {cw_count},
        color: 'purple',
        placeholder: 'Search CalWORKs policy: WTW hours, immediate need...',
        chips: [
          {{ label: 'Welfare-to-Work (30/35 hrs)', query: 'Welfare to Work 30 hours' }},
          {{ label: 'Immediate Need Cash ($200)', query: 'Immediate need emergency cash' }},
          {{ label: 'Property & Vehicle Exemptions', query: 'Property limitations vehicle exemption' }},
          {{ label: 'Maximum Aid Payment (MAP)', query: 'Maximum Aid Payment MAP' }}
        ]
      }},
      'Medi-Cal': {{
        title: 'Medi-Cal (Medicaid)',
        folder: 'Folder 599 (19 Official Articles & Special Notices)',
        total: {mc_count},
        color: 'sky',
        placeholder: 'Search Medi-Cal policy: MAGI income, postpartum coverage...',
        chips: [
          {{ label: 'Asset Limit Elimination (2024)', query: 'Asset test elimination 2024' }},
          {{ label: 'MAGI FPL 138% Income Limits', query: 'MAGI income eligibility Federal Poverty Level 138%' }},
          {{ label: 'Continuous Child Coverage (<5)', query: 'Continuous coverage for children under 5' }},
          {{ label: '12-Month Postpartum Coverage', query: 'Postpartum 12 months continuous' }}
        ]
      }},
      'All': {{
        title: 'All Programs',
        folder: 'Folders 542, 448, 599',
        total: {all_count},
        color: 'red',
        placeholder: 'Search all programs: CalFresh, CalWORKs, Medi-Cal...',
        chips: [
          {{ label: 'CalFresh Student Rules', query: 'CalFresh student eligibility' }},
          {{ label: 'CalWORKs WTW Hours', query: 'CalWORKs Welfare to Work hours' }},
          {{ label: 'Medi-Cal Asset Elimination', query: 'Medi-Cal asset limit elimination' }},
          {{ label: 'SAR 7 Reporting Requirements', query: 'Semi Annual Reporting SAR 7' }}
        ]
      }}
    }};

    // Day / dark mode. The choice is remembered on this device; without one, the device setting is used.
    function syncThemeToggle() {{
      const dark = document.documentElement.classList.contains('dark');
      const btn = document.getElementById('themeToggle');
      if (!btn) return;
      btn.setAttribute('aria-pressed', dark ? 'true' : 'false');
      btn.title = dark ? 'Switch to day mode' : 'Switch to dark mode';
      btn.querySelector('.theme-label').textContent = dark ? 'Day mode' : 'Dark mode';
    }}
    function toggleTheme() {{
      const dark = !document.documentElement.classList.contains('dark');
      document.documentElement.classList.toggle('dark', dark);
      try {{ localStorage.setItem('theme', dark ? 'dark' : 'light'); }} catch (e) {{}}
      syncThemeToggle();
    }}
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {{
      let saved = null;
      try {{ saved = localStorage.getItem('theme'); }} catch (err) {{}}
      if (!saved) {{ document.documentElement.classList.toggle('dark', e.matches); syncThemeToggle(); }}
    }});
    document.addEventListener('DOMContentLoaded', syncThemeToggle);

    // Close the "County guides" menu on an outside click or Escape.
    document.addEventListener('click', e => {{
      document.querySelectorAll('details.guides-menu[open]').forEach(d => {{ if (!d.contains(e.target)) d.open = false; }});
    }});
    document.addEventListener('keydown', e => {{
      if (e.key === 'Escape') document.querySelectorAll('details.guides-menu[open]').forEach(d => {{ d.open = false; }});
    }});

    function switchProgram(prog, opts = {{}}) {{
      activeProgram = prog;
      const meta = PROGRAM_METADATA[prog];

      // Update program tab styles
      ['All', 'CalFresh', 'CalWORKs', 'Medi-Cal'].forEach(p => {{
        const btn = document.getElementById('tab-' + p);
        if (btn) {{
          btn.classList.toggle('is-active', p === prog);
          btn.setAttribute('aria-pressed', p === prog ? 'true' : 'false');
        }}
      }});

      // Update input placeholder and visible / screen-reader scope hints
      const searchInp = document.getElementById('searchInput');
      if (searchInp) searchInp.placeholder = meta.placeholder;
      const scopeLabel = document.getElementById('searchScopeLabel');
      if (scopeLabel) scopeLabel.textContent = meta.title;
      const scopeChip = document.getElementById('searchScopeChip');
      if (scopeChip) scopeChip.textContent = prog === 'All' ? 'All programs' : prog;
      const scopeDesc = document.getElementById('searchScope');
      if (scopeDesc) scopeDesc.textContent = prog === 'All' ? 'Searching all program guides.' : 'Searching the ' + meta.title + ' guide.';

      if (opts.skipSearch) {{
        updateClearButtonVisibility();
        return;
      }}

      // Re-run search or display full program catalog
      const q = getSearchQuery();
      if (q) {{
        executeSearch(q, 'search');
      }} else {{
        cancelSearchToDropdowns();
      }}
    }}

    function clearSearch() {{
      const searchView = document.getElementById('searchResultsPageView');
      const onResultsPage = searchView && !searchView.classList.contains('hidden');
      if (onResultsPage) {{
        cancelSearchToDropdowns();
        return;
      }}
      setSearchQuery('');
      hideSearchError();
      updateSearchUrl('', 'search', {{ replace: true }});
      const el = document.getElementById('searchInput');
      if (el) el.focus();
    }}

    function handleSearchSubmit(e) {{
      e.preventDefault();
      const mode = (e.submitter && e.submitter.value) || 'search';
      handleSearchMode(mode);
    }}

    function handleSearchMode(mode) {{
      const q = getSearchQuery();
      if (!q) {{
        showSearchError('Enter a search term to search the policy manuals.');
        const el = document.getElementById('searchInput');
        if (el) el.focus();
        return;
      }}
      hideSearchError();
      executeSearch(q, mode === 'ask' ? 'ask' : 'search');
    }}

    function highlightMatchedText(text, query) {{
      if (!text || !query) return escapeHtml(text || '');
      const words = query.toLowerCase().split(/\s+/).filter(w => w.length > 2);
      if (words.length === 0) return escapeHtml(text);
      let escaped = escapeHtml(text);
      words.forEach(w => {{
        const safeW = w.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
        const reg = new RegExp('(' + safeW + ')', 'gi');
        escaped = escaped.replace(reg, '<mark class="bg-amber-200 text-amber-950 font-bold px-0.5 rounded">$1</mark>');
      }});
      return escaped;
    }}

    function filterDocs(query, prog) {{
      let filtered = EMBEDDED_DOCS;
      if (prog !== 'All') {{
        filtered = filtered.filter(d => (d.programs || []).includes(prog));
      }}
      if (!query) return filtered;

      const words = query.toLowerCase().split(/\s+/).filter(Boolean);
      const scored = [];

      filtered.forEach(d => {{
        const title = (d.title || '').toLowerCase();
        const chapter = (d.chapter || '').toLowerCase();
        const summary = (d.summary || '').toLowerCase();
        const body = (d.content_text || '').toLowerCase();

        let score = 0;
        let matchedTerms = [];
        words.forEach(w => {{
          if (title.includes(w)) {{ score += 12; matchedTerms.push(w); }}
          if (summary.includes(w)) {{ score += 6; matchedTerms.push(w); }}
          if (chapter.includes(w)) {{ score += 4; matchedTerms.push(w); }}
          if (body.includes(w)) {{ score += 3; matchedTerms.push(w); }}
        }});

        if (score > 0) {{
          let excerpt = '';
          const cleanBody = d.content_text || '';
          if (cleanBody && matchedTerms.length > 0) {{
            const pos = cleanBody.toLowerCase().indexOf(matchedTerms[0]);
            if (pos !== -1) {{
              const start = Math.max(0, pos - 70);
              const end = Math.min(cleanBody.length, pos + 160);
              excerpt = (start > 0 ? '...' : '') + cleanBody.slice(start, end).trim() + (end < cleanBody.length ? '...' : '');
            }}
          }}
          scored.push({{
            ...d,
            score: Math.round(score * 10) / 10,
            matched_excerpt: excerpt
          }});
        }}
      }});

      return scored.sort((a, b) => b.score - a.score);
    }}

    let activeSearchController = null;

    function setSearchBusy(busy, mode) {{
      const form = document.getElementById('searchForm');
      if (!form) return;
      const labels = {{ search: 'Search', ask: 'Ask AI' }};
      form.querySelectorAll('button[type="submit"]').forEach(btn => {{
        btn.disabled = busy;
        btn.classList.toggle('is-active', busy ? btn.value === mode : btn.value === 'search');
        const label = btn.querySelector('[data-label]');
        if (!label) return;
        label.textContent = (busy && btn.value === mode)
          ? (btn.value === 'ask' ? 'Asking…' : 'Searching…')
          : labels[btn.value];
      }});
      form.setAttribute('aria-busy', busy ? 'true' : 'false');
    }}

    function focusSearchResultsHeading() {{
      const heading = document.getElementById('searchResultsHeading');
      const view = document.getElementById('searchResultsPageView');
      if (view) view.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      if (heading) {{
        try {{ heading.focus({{ preventScroll: true }}); }} catch (err) {{ heading.focus(); }}
      }}
    }}

    // "Showing results for eligibility. Search instead for eligibilty" when the
    // server fixed a misspelled word (see correct_query in search_engine.py).
    function showSearchCorrection(info) {{
      const box = document.getElementById('searchCorrection');
      if (!box) return;
      box.replaceChildren();
      box.classList.toggle('hidden', !info);
      if (!info) return;
      box.append('Showing results for ');
      const fixed = document.createElement('strong');
      fixed.textContent = info.corrected;
      box.append(fixed, '. ');
      const instead = document.createElement('button');
      instead.type = 'button';
      instead.className = 'underline text-blue-700 hover:text-blue-900 cursor-pointer';
      instead.textContent = 'Search instead for "' + info.original + '"';
      instead.addEventListener('click', () => executeSearch(info.original, info.mode, {{ exact: true, skipHistory: true }}));
      box.append(instead);
    }}

    async function executeSearch(query, mode, opts = {{}}) {{
      const prog = activeProgram;

      if (!query || !query.trim()) {{
        cancelSearchToDropdowns();
        return;
      }}

      // Abort any earlier request so a stale response cannot overwrite this one.
      if (activeSearchController) activeSearchController.abort();
      const controller = new AbortController();
      activeSearchController = controller;

      if (!opts.skipHistory) {{
        updateSearchUrl(query, mode, {{ replace: !!opts.replaceHistory }});
      }}

      // Switch to Dedicated Search Results Page
      const manualView = document.getElementById('manualDropdownsView');
      const searchView = document.getElementById('searchResultsPageView');
      if (manualView) manualView.classList.add('hidden');
      if (searchView) searchView.classList.remove('hidden');

      // Update Top Search Results Header Info
      const scopeBadge = document.getElementById('searchResultScopeBadge');
      const queryText = document.getElementById('searchResultQueryText');
      const countText = document.getElementById('searchResultCountText');

      if (scopeBadge) scopeBadge.textContent = prog === 'All' ? 'All Programs' : prog;
      if (queryText) queryText.textContent = `"${{query}}"`;
      if (countText) countText.textContent = 'Searching official policy documents...';

      hideSearchError();
      setSearchBusy(true, mode);

      if (mode === 'ask') {{
        showAIAnswerLoading();
      }} else {{
        const aiContainer = document.getElementById('aiAnswerContainer');
        if (aiContainer) aiContainer.classList.add('hidden');
      }}

      // Start both requests at once so the AI answer never delays the document list.
      showSearchCorrection(null);
      const searchPromise = fetch(LOCAL_SERVER_BASE + '/api/search?q=' + encodeURIComponent(query) + '&program=' + encodeURIComponent(prog) + '&limit=150' + (opts.exact ? '&exact=1' : ''), {{ signal: controller.signal }})
        .then(resp => resp.ok ? resp.json() : null)
        .catch(err => {{
          if (err && err.name === 'AbortError') throw err;
          console.log('Using client-side full-text search fallback:', err);
          return null;
        }});

      let aiPromise = null;
      if (mode === 'ask') {{
        aiPromise = fetch(LOCAL_SERVER_BASE + '/api/ask', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ question: query, program: prog }}),
          signal: controller.signal
        }})
          .then(resp => resp.ok ? resp.json() : null)
          .catch(err => {{
            if (err && err.name === 'AbortError') throw err;
            console.warn('Backend /api/ask unavailable, using client-side synthesis:', err);
            return null;
          }});
      }}

      try {{
        let apiDocs = null;
        const data = await searchPromise;
        if (controller.signal.aborted) return;
        showSearchCorrection(data && data.corrected_query ? {{ corrected: data.corrected_query, original: query, mode }} : null);

        if (data && data.results && data.results.length > 0) {{
          const docMap = {{}};
          EMBEDDED_DOCS.forEach(d => {{ docMap[d.id] = d; }});
          apiDocs = data.results.map(r => {{
            const base = docMap[r.id] || {{}};
            return {{
              ...base,
              ...r,
              category: base.category || r.category || 'General Sections',
              order: base.order || 50,
              category_desc: base.category_desc || '',
              category_id: base.category_id || 'cat-general'
            }};
          }});
        }}

        const docs = apiDocs || filterDocs(query, prog);
        if (countText) {{
          countText.textContent = `${{docs.length}} matching official policy document${{docs.length === 1 ? '' : 's'}} (Ranked by BM25 Relevance)`;
        }}
        renderSearchResultsView(docs, query);
        if (opts.focusResults !== false) focusSearchResultsHeading();
      }} catch (err) {{
        if (err && err.name === 'AbortError') return;
        const docs = filterDocs(query, prog);
        if (countText) {{
          countText.textContent = `${{docs.length}} matching official policy document${{docs.length === 1 ? '' : 's'}}`;
        }}
        renderSearchResultsView(docs, query);
      }} finally {{
        if (activeSearchController === controller) {{
          setSearchBusy(false, mode);
        }}
      }}

      if (aiPromise) {{
        try {{
          const aiData = await aiPromise;
          if (controller.signal.aborted) return;
          if (aiData && aiData.answer) {{
            renderAIAnswer(aiData.answer, aiData.sources || []);
          }} else {{
            synthesizeClientAnswer(query, prog);
          }}
        }} catch (err) {{
          if (!err || err.name !== 'AbortError') synthesizeClientAnswer(query, prog);
        }}
      }}
    }}

    function showAIAnswerLoading() {{
      const container = document.getElementById('aiAnswerContainer');
      if (!container) return;
      container.classList.remove('hidden');
      document.getElementById('aiScopeTag').innerText = activeProgram === 'All' ? 'All Programs' : activeProgram + ' Isolated';
      document.getElementById('aiAnswerText').innerHTML = `
        <div class="flex items-center gap-2 text-blue-700 py-3">
          <svg class="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span class="font-medium text-xs">Analyzing official policy guides and generating answer...</span>
        </div>
      `;
      document.getElementById('aiSourcesList').innerHTML = '';
    }}

    function renderAIAnswer(answerText, sources) {{
      const container = document.getElementById('aiAnswerContainer');
      if (!container) return;
      container.classList.remove('hidden');
      document.getElementById('aiScopeTag').innerText = activeProgram === 'All' ? 'All Programs' : activeProgram + ' Isolated';

      const scopeBadge = activeProgram !== 'All' 
        ? `<div class="mb-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-blue-100 text-blue-900 font-bold text-xs">
             <span>✓ Scoped strictly to ${{activeProgram}} (${{PROGRAM_METADATA[activeProgram].folder}})</span>
           </div>`
        : `<div class="mb-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-red-100 text-red-900 font-bold text-xs">
             <span>Cross-Program Search (All 3 County Benefit Guides)</span>
           </div>`;

      document.getElementById('aiAnswerText').innerHTML = scopeBadge + '<div class="leading-relaxed">' + escapeHtml(answerText).replace(/\\n/g, '<br>') + '</div>';

      const sourcesList = document.getElementById('aiSourcesList');
      sourcesList.innerHTML = '';
      if (sources && sources.length > 0) {{
        sources.forEach(s => {{
          const el = document.createElement('div');
          el.className = 'bg-white border border-blue-200 rounded-lg p-2.5 text-xs shadow-2xs flex flex-col justify-between';
          const localPdf = escapeHtml(pdfViewerUrl(docOpenUrl(s)));
          el.innerHTML = `
            <div class="mb-2">
              <div class="font-bold text-slate-800 line-clamp-1">${{escapeHtml(s.title)}}</div>
              <div class="mt-2 p-3.5 bg-blue-50/70 border border-blue-100 rounded-lg text-xs sm:text-[15px] text-slate-700 leading-relaxed">
                <span class="font-bold text-blue-900 block text-xs mb-1">Quick PDF Summary:</span>
                ${{docDateHtml(s)}}
                ${{escapeHtml(s.summary || s.snippet || '')}}
              </div>
            </div>
            <div class="flex items-center justify-between pt-1 border-t border-slate-100 text-xs">
              <span class="font-semibold text-blue-600">${{(s.programs || []).join(', ')}}</span>
              <div class="flex items-center gap-1.5">
                <button type="button" onclick="viewDocPdf('${{s.id}}')" class="bg-emerald-600 hover:bg-emerald-700 text-white px-2.5 py-1 rounded font-bold transition inline-flex items-center gap-1 shadow-2xs cursor-pointer">
                  <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/></svg>
                  <span>${{isSourceMissing(s) ? 'County Site' : 'View in Page'}}</span>
                </button>
                <a href="${{localPdf}}" target="_blank" class="bg-red-600 hover:bg-red-700 text-white p-1 rounded transition" title="Open in dedicated tab">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                </a>
              </div>
            </div>
          `;
          sourcesList.appendChild(el);
        }});
      }} else {{
        sourcesList.innerHTML = '<span class="text-xs text-slate-400">No specific sections cited.</span>';
      }}
    }}

    function synthesizeClientAnswer(query, prog) {{
      const matches = filterDocs(query, prog);
      if (matches.length === 0) {{
        renderAIAnswer(`No policy sections found in the **${{prog}}** guide matching "${{query}}". Please try different search keywords or switch to "All Programs" to search across CalFresh, CalWORKs, and Medi-Cal.`, []);
        return;
      }}
      const topMatch = matches[0];
      const answer = `Based on County of San Diego **${{topMatch.programs.join('/')}}** policy manual (**${{topMatch.title}}**):\\n\\n` +
        `• **Quick Policy Summary**: ${{docDateLine(topMatch) ? docDateLine(topMatch) + '. ' : ''}}${{topMatch.summary || topMatch.snippet.slice(0, 300)}}\\n\\n` +
        `This policy rule applies strictly under ${{topMatch.programs.join('/')}} guidelines. For full administrative regulations, open the complete official PDF linked below.`;

      renderAIAnswer(answer, matches.slice(0, 4));
    }}

    function resolveLocalPdfUrl(pdfUrl, docId) {{
      if (pdfUrl && pdfUrl.startsWith('/pdfs/')) {{
        return (LOCAL_SERVER_BASE || '') + pdfUrl;
      }}
      if (pdfUrl && pdfUrl.startsWith('http')) {{
        return pdfUrl;
      }}
      return (LOCAL_SERVER_BASE || '') + '/pdfs/' + encodeURIComponent(docId) + '.pdf';
    }}

    // "Revision date: April 1, 2023" - the date taken from the document's own PDF.
    // Old Medi-Cal sections are dated to the month only ("2001-01" -> "January 2001").
    function formatLongDate(iso) {{
      const m = /^(\d{{4}})-(\d{{2}})(?:-(\d{{2}}))?/.exec(iso || '');
      if (!m) return '';
      const d = new Date(Date.UTC(+m[1], +m[2] - 1, m[3] ? +m[3] : 1));
      const parts = m[3] ? {{ year: 'numeric', month: 'long', day: 'numeric' }} : {{ year: 'numeric', month: 'long' }};
      return d.toLocaleDateString('en-US', Object.assign(parts, {{ timeZone: 'UTC' }}));
    }}

    function docDateLine(doc) {{
      const base = (doc && DOCS_BY_ID[doc.id]) || {{}};
      const iso = (doc && doc.pdf_date) || base.pdf_date;
      const label = (doc && doc.pdf_date_label) || base.pdf_date_label;
      const text = formatLongDate(iso);
      return text ? (label || 'PDF date') + ': ' + text : '';
    }}

    // Where the date came from, shown on hover.
    function docDateHint(doc) {{
      const base = (doc && DOCS_BY_ID[doc.id]) || doc || {{}};
      const label = base.pdf_date_label || '';
      if (label === 'PDF file date') return 'No date is printed in this document, so this is the date stored in the PDF file.';
      if (label === 'Latest MPG letter') return 'No revision date is printed in this section, so this is the newest MPG letter printed on its pages.';
      if (label.startsWith('Latest ')) return 'This document combines several sections; this is the newest date printed in any of them.';
      return 'Printed in the document.';
    }}

    function docDateHtml(doc) {{
      const line = docDateLine(doc);
      if (!line) return '';
      return `<div class="mb-1.5 text-xs font-bold text-emerald-800" title="${{docDateHint(doc)}}">${{escapeHtml(line)}}</div>`;
    }}

    // The County changed this PDF after its summary was written (summaries.py marks it stale).
    function summaryStale(doc) {{
      const base = (doc && DOCS_BY_ID[doc.id]) || doc || {{}};
      return base.summary_status === 'stale';
    }}

    // Entries without a bundled County document link out to the County site.
    function isSourceMissing(doc) {{
      const base = (doc && DOCS_BY_ID[doc.id]) || doc || {{}};
      return !!(base.source_missing || (doc && doc.source_missing));
    }}

    function docOpenUrl(doc) {{
      if (isSourceMissing(doc)) {{
        const base = DOCS_BY_ID[doc.id] || doc;
        return base.official_url || doc.official_url || '#';
      }}
      return resolveLocalPdfUrl(doc.local_pdf_url, doc.id);
    }}

    // PDFs open in the bundled PDF.js viewer (static/pdfjs), which has its own
    // find bar. When a site search is showing, its words are passed along so
    // the matches are highlighted as the document opens.
    // Bump the v= value after changing static/pdfjs so browsers fetch the new viewer page.
    const PDF_VIEWER_URL = (LOCAL_SERVER_BASE || '') + '/pdfjs/web/viewer.html?v=6.5.438-2';
    const PDF_SEARCH_SKIP = new Set(['a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'can', 'do', 'does', 'for', 'from',
      'how', 'i', 'if', 'in', 'is', 'it', 'my', 'of', 'on', 'or', 'the', 'to', 'what', 'when', 'who', 'with']);

    function pdfSearchTerms() {{
      const view = document.getElementById('searchResultsPageView');
      if (!view || view.classList.contains('hidden')) return '';
      const words = (getSearchQuery() || '').replace(/["“”]/g, ' ').split(/\s+/)
        .filter(w => w.length > 1 && !PDF_SEARCH_SKIP.has(w.toLowerCase()));
      return words.slice(0, 8).join(' ');
    }}

    function pdfViewerUrl(pdfUrl) {{
      // Only stored PDFs go through the viewer; County links open as they are.
      if (!pdfUrl || !pdfUrl.startsWith((LOCAL_SERVER_BASE || '') + '/pdfs/')) return pdfUrl;
      const terms = pdfSearchTerms();
      return PDF_VIEWER_URL + '&file=' + encodeURIComponent(pdfUrl) + (terms ? '#search=' + encodeURIComponent(terms) : '');
    }}

    // In-Page PDF Viewer Modal Functions
    function openPdfModal(pdfUrl, title, program, summary, section) {{
      const modal = document.getElementById('pdfViewerModal');
      const iframe = document.getElementById('pdfViewerFrame');
      const titleEl = document.getElementById('pdfModalTitle');
      const badgeEl = document.getElementById('pdfModalProgramBadge');
      const metaEl = document.getElementById('pdfModalMeta');
      const summaryBar = document.getElementById('pdfModalSummaryBar');
      const summaryEl = document.getElementById('pdfModalSummaryText');
      const newTabBtn = document.getElementById('pdfModalNewTabBtn');
      const downloadBtn = document.getElementById('pdfModalDownloadBtn');
      const loading = document.getElementById('pdfModalLoading');

      if (!modal || !iframe) return;

      titleEl.textContent = title || 'Policy Document';
      badgeEl.textContent = program || 'HHSA';
      metaEl.textContent = (section ? ('Section: ' + section + ' • ') : '') + 'Official County of San Diego Policy PDF';
      
      // The summary starts collapsed so the document gets the full height;
      // the "Summary" button opens it.
      summaryEl.textContent = (summary && summary.trim()) ? summary : 'No summary is available for this document.';
      setModalSummaryOpen(false);

      newTabBtn.href = pdfViewerUrl(pdfUrl);
      if (downloadBtn) {{
        downloadBtn.href = pdfUrl;
        downloadBtn.setAttribute('download', (section ? (section + ' - ') : '') + (title || 'document') + '.pdf');
      }}

      loading.classList.remove('hidden');
      iframe.src = pdfViewerUrl(pdfUrl);

      modal.classList.remove('hidden');
      modal.classList.add('flex');
      document.body.classList.add('overflow-hidden');
    }}

    function closePdfModal() {{
      const modal = document.getElementById('pdfViewerModal');
      const iframe = document.getElementById('pdfViewerFrame');
      if (!modal) return;
      modal.classList.add('hidden');
      modal.classList.remove('flex');
      if (iframe) iframe.src = 'about:blank';
      document.body.classList.remove('overflow-hidden');
    }}

    function setModalSummaryOpen(open) {{
      const summaryBar = document.getElementById('pdfModalSummaryBar');
      const summaryBtn = document.getElementById('pdfModalSummaryBtn');
      if (summaryBar) summaryBar.classList.toggle('hidden', !open);
      if (summaryBtn) summaryBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    }}

    function toggleModalSummary() {{
      const summaryBar = document.getElementById('pdfModalSummaryBar');
      if (summaryBar) setModalSummaryOpen(summaryBar.classList.contains('hidden'));
    }}

    function viewDocPdf(docId, fallbackUrl, fallbackTitle, fallbackProg, fallbackSummary) {{
      let doc = DOCS_BY_ID[docId];
      if (!doc) {{
        doc = {{
          id: docId,
          title: fallbackTitle || docId,
          programs: fallbackProg ? [fallbackProg] : ['HHSA'],
          summary: fallbackSummary || '',
          local_pdf_url: fallbackUrl || ''
        }};
      }}
      if (isSourceMissing(doc)) {{
        window.open(docOpenUrl(doc), '_blank', 'noopener');
        return;
      }}
      const pdfUrl = resolveLocalPdfUrl(doc.local_pdf_url, doc.id);
      const dateLine = docDateLine(doc);
      openPdfModal(pdfUrl, doc.title, (doc.programs || []).join(' / '), (dateLine ? dateLine + '. ' : '') + (doc.summary || doc.snippet || ''), doc.chapter || doc.id);
    }}

    // Close modal or return from search results page on Escape key
    document.addEventListener('keydown', (e) => {{
      if (e.key === 'Escape') {{
        const modal = document.getElementById('pdfViewerModal');
        if (modal && !modal.classList.contains('hidden')) {{
          closePdfModal();
          return;
        }}
        const searchView = document.getElementById('searchResultsPageView');
        if (searchView && !searchView.classList.contains('hidden')) {{
          cancelSearchToDropdowns();
        }}
      }}
    }});

    document.addEventListener('click', (e) => {{
      const modal = document.getElementById('pdfViewerModal');
      if (modal && !modal.classList.contains('hidden') && e.target === modal) {{
        closePdfModal();
      }}
    }});

    function createDocumentCard(doc, query) {{
      const card = document.createElement('div');
      card.className = 'border border-slate-200 hover:border-blue-400 rounded-xl p-3.5 sm:p-4.5 shadow-2xs hover:shadow-xs transition flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white';
      
      const progBadgeColor = doc.programs.includes('CalFresh') 
        ? 'bg-emerald-100 text-emerald-800 border-emerald-200' 
        : doc.programs.includes('CalWORKs') 
          ? 'bg-purple-100 text-purple-800 border-purple-200' 
          : 'bg-teal-100 text-teal-800 border-teal-200';

      const localPdfLink = escapeHtml(pdfViewerUrl(docOpenUrl(doc)));
      const missing = isSourceMissing(doc);
      const revisionStr = doc.published_on ? doc.published_on.slice(0, 10) : 'Not available';

      let secBadgeHtml = '';
      if (doc.section_num) {{
        let badgeColor = 'bg-slate-100 text-slate-800 border-slate-300';
        if (doc.programs.includes('CalWORKs')) {{
          badgeColor = 'bg-purple-100 text-purple-900 border-purple-300';
        }} else if (doc.programs.includes('Medi-Cal')) {{
          badgeColor = 'bg-teal-100 text-teal-900 border-teal-300';
        }} else if (doc.programs.includes('CalFresh')) {{
          badgeColor = 'bg-emerald-100 text-emerald-900 border-emerald-300';
        }}
        let label = doc.section_num;
        if (!label.toLowerCase().startsWith('section') && !label.toLowerCase().startsWith('sn')) {{
          label = 'Section ' + label;
        }}
        secBadgeHtml = `<span class="px-2 py-0.5 rounded text-xs font-mono font-extrabold ${{badgeColor}} border shadow-2xs">${{escapeHtml(label)}}</span>`;
      }}

      card.innerHTML = `
        <div class="flex-1 min-w-0">
          <div class="flex flex-wrap items-center gap-2 mb-1.5">
            <span class="px-2 py-0.5 rounded text-xs font-bold border ${{progBadgeColor}}">${{(doc.programs || []).join(' / ')}}</span>
            ${{secBadgeHtml}}
            <span class="font-bold text-slate-800 text-xs sm:text-sm">${{escapeHtml(doc.title)}}</span>
            ${{missing ? '<span class="px-2 py-0.5 rounded text-xs font-bold border bg-amber-100 text-amber-900 border-amber-300">County document not bundled</span>' : ''}}
            ${{summaryStale(doc) ? '<span class="px-2 py-0.5 rounded text-xs font-bold border bg-amber-100 text-amber-900 border-amber-300" title="The County updated this PDF after the summary was written. Check the PDF.">Summary under review</span>' : ''}}
          </div>

          <!-- Quick PDF Summary Everywhere -->
          <div class="my-3 p-4 sm:p-5 bg-white border-[1.5px] border-black rounded-2xl text-[15px] sm:text-sm text-slate-800 leading-relaxed shadow-xs">
            <div class="flex items-center gap-2 text-blue-900 font-bold mb-2 text-xs sm:text-sm tracking-wide">
              <svg class="w-4 h-4 sm:w-4.5 sm:h-4.5 text-blue-600 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path></svg>
              <span>Quick Policy Summary:</span>
            </div>
            ${{docDateHtml(doc)}}
            <div class="text-slate-800 font-normal leading-relaxed text-[15px] sm:text-sm">
              ${{escapeHtml(doc.summary || doc.snippet || 'Official County of San Diego Health and Human Services Agency Policy Document.')}}
            </div>
          </div>

          <!-- Deep PDF Body Match (if query matched inside PDF) -->
          ${{doc.matched_excerpt ? `
            <div class="my-2 p-2.5 bg-amber-50/90 border border-amber-300 rounded-lg text-xs text-slate-800 leading-relaxed shadow-2xs">
              <div class="flex items-center justify-between mb-1.5 text-[13px]">
                <span class="font-bold text-amber-950 flex items-center gap-1.5">
                  <svg class="w-3.5 h-3.5 text-amber-700 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path></svg>
                  <span>Matched PDF Body Passage:</span>
                </span>
                <span class="bg-amber-200 text-amber-950 font-bold text-[12px] px-1.5 py-0.5 rounded border border-amber-300">
                  BM25 Score: ${{doc.score || 'Full Text Match'}}
                </span>
              </div>
              <div class="font-mono text-[13px] text-slate-800 bg-white/80 p-2 rounded border border-amber-200/80">
                ${{highlightMatchedText(doc.matched_excerpt, query)}}
              </div>
            </div>
          ` : ''}}

          <div class="flex items-center gap-3 text-xs text-slate-400 mt-1">
            <span>Section: <strong class="text-slate-600">${{escapeHtml(doc.section_num ? (doc.section_num + (doc.section_title ? (' • ' + doc.section_title) : '')) : (doc.chapter || doc.id))}}</strong></span>
            <span>•</span>
            <span>Posted on County site: ${{revisionStr}}</span>
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0 w-full sm:w-auto justify-end pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100">
          <button type="button" onclick="viewDocPdf('${{doc.id}}')" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-3.5 py-2 rounded-lg transition inline-flex items-center gap-1.5 shadow-2xs cursor-pointer">
            <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/></svg>
            <span>${{missing ? 'Open County Site' : 'View PDF in Page'}}</span>
          </button>
          <a href="${{localPdfLink}}" target="_blank" class="bg-red-600 hover:bg-red-700 text-white text-xs font-bold px-2.5 py-2 rounded-lg transition inline-flex items-center gap-1 shadow-2xs" title="Open in new window or tab">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
            <span class="hidden md:inline">New Tab</span>
          </a>
        </div>
      `;
      return card;
    }}

__CHAPTER_NAV_JS__

    function renderSearchResultsView(docs, query) {{
      const container = document.getElementById('searchResultsList');
      if (!container) return;
      container.innerHTML = '';

      if (docs.length === 0) {{
        container.innerHTML = `
          <div class="bg-amber-50 border border-amber-200 rounded-xl p-8 text-center text-amber-900 text-xs shadow-xs">
            <div class="w-12 h-12 bg-amber-100 text-amber-700 rounded-full flex items-center justify-center mx-auto mb-3 font-bold text-lg">
              🔍
            </div>
            <h4 class="font-bold text-sm sm:text-base text-amber-950 mb-1">No matching policy documents found for "${{escapeHtml(query)}}"</h4>
            <p class="text-slate-600 mb-4 max-w-md mx-auto">No policy sections or regulations matched your search query in the current guide. Try broader keywords or search across all County benefit programs.</p>
            <div class="flex items-center justify-center gap-3">
              <button type="button" onclick="cancelSearchToDropdowns()" class="bg-white hover:bg-slate-100 text-slate-800 border border-slate-300 font-bold px-4 py-2 rounded-lg transition cursor-pointer">
                ← Back to Chapter Dropdowns
              </button>
              <button type="button" id="searchAllProgramsBtn" class="bg-red-600 hover:bg-red-700 text-white font-bold px-4 py-2 rounded-lg transition shadow-xs cursor-pointer">
                Search All Programs
              </button>
            </div>
          </div>
        `;
        const allBtn = document.getElementById('searchAllProgramsBtn');
        if (allBtn) {{
          allBtn.onclick = () => {{
            switchProgram('All', {{ skipSearch: true }});
            executeSearch(query, 'search');
          }};
        }}
        return;
      }}

      docs.forEach(doc => {{
        container.appendChild(createDocumentCard(doc, query));
      }});
    }}

    function cancelSearchToDropdowns(opts = {{}}) {{
      if (activeSearchController) {{
        activeSearchController.abort();
        activeSearchController = null;
      }}
      setSearchQuery('');
      hideSearchError();
      setSearchBusy(false);
      const manualView = document.getElementById('manualDropdownsView');
      const searchView = document.getElementById('searchResultsPageView');
      const aiContainer = document.getElementById('aiAnswerContainer');

      if (searchView) searchView.classList.add('hidden');
      if (manualView) manualView.classList.remove('hidden');
      if (aiContainer) aiContainer.classList.add('hidden');

      if (opts.updateHistory !== false) {{
        updateSearchUrl('', 'search', {{ replace: true }});
      }}

      // Refresh default dropdowns view
      const currentDocs = filterDocs('', activeProgram);
      renderDropdownsView(currentDocs);
    }}

    // Keep the URL in sync with the browser's back/forward buttons.
    window.addEventListener('popstate', () => {{
      const state = readSearchStateFromUrl();
      setSearchQuery(state.query);
      switchProgram(state.program, {{ skipSearch: true }});
      if (state.query) {{
        executeSearch(state.query, state.mode, {{ replaceHistory: true, focusResults: false }});
      }} else {{
        cancelSearchToDropdowns({{ updateHistory: false }});
      }}
    }});

    // "/" or Cmd/Ctrl+K focuses the search box from anywhere on the page.
    document.addEventListener('keydown', (e) => {{
      if (e.defaultPrevented) return;
      const el = document.activeElement;
      const isTyping = el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT' || el.isContentEditable);
      const isShortcut = (e.key === '/' && !isTyping) || ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k');
      if (!isShortcut) return;
      e.preventDefault();
      const input = document.getElementById('searchInput');
      if (input) {{
        input.focus();
        input.select();
      }}
    }});

    // Restore search state from the URL, then wire up input feedback.
    document.addEventListener('DOMContentLoaded', () => {{
      const state = readSearchStateFromUrl();
      setSearchQuery(state.query);
      switchProgram(state.program, {{ skipSearch: true }});

      if (state.query) {{
        executeSearch(state.query, state.mode, {{ replaceHistory: true, focusResults: false }});
      }} else {{
        cancelSearchToDropdowns();
      }}

      const searchInp = document.getElementById('searchInput');
      if (searchInp) {{
        searchInp.addEventListener('input', () => {{
          updateClearButtonVisibility();
          hideSearchError();
          if (!searchInp.value.trim()) {{
            const searchView = document.getElementById('searchResultsPageView');
            if (searchView && !searchView.classList.contains('hidden')) {{
              cancelSearchToDropdowns();
            }}
          }}
        }});
      }}
      updateClearButtonVisibility();
    }});
  </script>
  <!-- Back to top: appears once the reader has scrolled down. -->
  <button type="button" id="backToTopBtn" aria-label="Back to top" title="Back to top"
    class="hidden fixed bottom-5 right-5 z-40 flex items-center gap-1.5 bg-[#0b2545] hover:bg-blue-800 text-white font-semibold text-sm p-3 sm:px-4 sm:py-2.5 rounded-full shadow-lg border border-white/20 cursor-pointer">
    <svg class="w-5 h-5 sm:w-4 sm:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 15l7-7 7 7"></path></svg>
    <span class="hidden sm:inline">Back to top</span>
  </button>
  <script>
    (function () {{
      const btn = document.getElementById('backToTopBtn');
      if (!btn) return;
      const update = () => {{ btn.classList.toggle('hidden', window.scrollY < 600); }};
      window.addEventListener('scroll', update, {{ passive: true }});
      btn.addEventListener('click', () => {{
        const smooth = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        window.scrollTo({{ top: 0, behavior: smooth ? 'smooth' : 'auto' }});
      }});
      update();
    }})();
  </script>
</body>
</html>"""

# Generate templates/index.html for server.py
def _read_template(name):
    with open(os.path.join(BASE_DIR, "templates", name), "r", encoding="utf-8") as f:
        return f.read().rstrip("\n")

web_html = (html_template
            .replace('__SERVER_BASE__', '')
            .replace('__CHAPTER_NAV_CSS__', _read_template("chapter_nav.css"))
            .replace('__THEME_CSS__', _read_template("theme.css"))
            .replace('__CHAPTER_NAV_JS__', _read_template("chapter_nav.js")))
with open(TEMPLATE_PATH, 'w', encoding='utf-8') as f:
    f.write(web_html)

print(f"Generated {TEMPLATE_PATH} ({os.path.getsize(TEMPLATE_PATH)} bytes)")
