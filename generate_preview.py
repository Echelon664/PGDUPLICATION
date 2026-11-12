#!/usr/bin/env python3
import json, html, os, re

ARTIFACT_PATH = "/Users/echelon619/.gemini/antigravity/brain/df70e671-e6fb-4e6d-b828-18340155569b/web_preview.html"
TEMPLATE_PATH = "/Users/echelon619/.gemini/antigravity/scratch/sd-benefits-search/templates/index.html"
DOCS_PATH = "/Users/echelon619/.gemini/antigravity/scratch/sd-benefits-search/data/documents.json"

with open(DOCS_PATH, 'r', encoding='utf-8') as f:
    full_docs = json.load(f)

print(f"Loaded {len(full_docs)} unique documents.")

cf_count = sum(1 for d in full_docs if 'CalFresh' in d.get('programs', []))
cw_count = sum(1 for d in full_docs if 'CalWORKs' in d.get('programs', []))
mc_count = sum(1 for d in full_docs if 'Medi-Cal' in d.get('programs', []))
all_count = len(full_docs)

print(f"Counts: CalFresh={cf_count}, CalWORKs={cw_count}, Medi-Cal={mc_count}, All={all_count}")

CHAPTER_DESCRIPTIONS = {
    # CalFresh (Folder 542) - 22 Official County Chapters & Special Notices
    '63-100 Application Process': 'Household concept, application filing, expedited service, interviews, and verification',
    '63-150 Non-Financial': 'Identity, residency, citizenship, non-citizen status, CFAP, student rules, and work quit',
    '63-200 Resources': 'Resource eligibility determination, liquid assets, and excluded resources',
    '63-220 Income': 'Earned income, unearned income, income exclusions, and self-employment',
    '63-230 Income Deductions': 'Standard deduction, earned income deduction, excess medical, dependent care, and shelter costs',
    '63-240 Households with Special Circumstances': 'Substantial lottery or gambling winnings and specialized eligibility',
    '63-250 Budgeting and Benefit Calculation': 'Prospective budgeting, reasonably anticipated income, migrant farmworkers, and allotment tables',
    '63-270 Semi-Annual Reporting': 'Semi-Annual Reporting (SAR), SAR cycle, and mandatory SAR 7 report processing',
    '63-280 Mid-Period Reporting': 'Voluntary and mandatory mid-period changes, IRT reporting, overissuances, and underissuances',
    '63-300 Certification': 'Certification periods, household classification, Notices of Action (NOA), and recertification',
    '63-320 Transitional CalFresh': 'Transitional CalFresh (TCF) benefits following CalWORKs cash aid discontinuance',
    '63-330 CalFresh Expansion for SSI-SSP Recipients': 'SSI/SSP expansion, Supplemental Nutrition Benefit (SNB), and Transitional Nutrition Benefit (TNB)',
    '63-350 Case Management': 'Case assignment, confidentiality, client requests, case record inspections, and intercounty transfers',
    '63-360 Elderly Simplified Application Project': 'ESAP streamlined certification and 36-month certification periods for elderly/disabled units',
    '63-370 Minimum Nutrition Benefit (MNB) Pilot Program': 'Minimum Nutrition Benefit state pilot program guidelines and supplemental allotments',
    '63-380 Prepared Meal Programs': 'Authorized restaurant meals, communal dining, and prepared meal purchases for eligible households',
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
    '10-009 Home Visiting Program': 'Voluntary nurse home visits, early childhood development, and prenatal/parenting support',
    '10-010 Child Care': 'Stage One child care eligibility, provider authorization, payment rules, and NOA requirements',
    '10-011 Supportive Services': 'Transportation reimbursement, work-related expenses, tools/uniforms, and mental health/substance abuse support',
    '10-020 Exemptions & Good Cause': 'Welfare-to-Work participation exemptions and good cause criteria',
    '10-025 Compliance Process': 'Noncompliance conciliation, cause determinations, compliance plans, and sanction cure procedures',
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
    '40-100 Application and Redetermination': 'Application intake, 45-day processing, Immediate Need cash ($200), redeterminations, and ICT',
    '40-125 Restoration of Aid': 'Expedited restoration of aid following discontinuance within 12 months',
    '40-183 CalWORKs Special Programs': 'Approved Relative Caregiver (ARC), extended CalWORKs for non-minor dependents (NMD), and family reunification',
    '41-400 Deprivation': 'Parental deprivation factors: unemployment (U-parent), absence, physical/mental incapacity, or death',
    '41-500 Assistance Unit': 'Assistance unit (AU) composition, mandatory inclusion rules, caretaker relatives, and temporary absence',
    '42-100 Age-Immunization-School Attendance': 'Age limits, school attendance mandates for children under 16, and preschool immunization requirements',
    '42-200 Property': 'Real and personal property limitations ($11,634 / $15,873), vehicle exemptions, and resource evaluation',
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
    'ARTICLE 08 - Responsible Relatives & Unit Determination': 'Medi-Cal family budget units (MFBU), tax dependency, and spousal allocations',
    'ARTICLE 09 - Property': 'Real and personal property evaluation, principal residence, and transfers',
    'ARTICLE 10 - NON-MAGI INCOME': 'Earned/unearned income, deductions, and Non-MAGI budgeting computations',
    'ARTICLE 11 - Maintenance Needs': 'Maintenance need standards and basic subsistence income levels',
    'ARTICLE 12 - Share-of-Cost': 'Share of Cost (SOC) determination, liability computation, and form processing',
    'ARTICLE 13 - PERIOD OF ELIGIBILITY': 'Retroactive coverage, ongoing eligibility periods, and continuous coverage',
    'ARTICLE 14 - MEDI-CAL CARD USE AND ISSUANCE': 'Benefits Identification Card (BIC) issuance, replacements, and authorization letters',
    'ARTICLE 15 - OTHER HEALTH CARE COVERAGE AND MEDICARE BUY-IN COVERAGE': 'Other Health Coverage (OHC), third-party liability, and Medicare Part A/B buy-in',
    'ARTICLE 16 - OVERPAYMENTS, FRAUD AND IMPROPER UTILIZATION': 'Fraud prevention, estate recovery, administrative disqualification, and overpayments',
    'ARTICLE 17 - MEDI-CAL SPECIAL TREATMENT PROGRAMS': 'Kidney transplant, organ anti-rejection, dialysis, and parenteral nutrition programs',
    'ARTICLE 20 - PERFORMANCE STANDARDS': 'Casework processing standards, redetermination timelines, and MEDS alerts',
    'ARTICLE 21 - MAGI APTC and Health Care Reform': 'Modified Adjusted Gross Income (MAGI), Covered CA, tax households, and ACA rules',
    'Special Notices & Policy Bulletins': 'County Medi-Cal Bulletins, COLA notices, emergency directives, and annual adjustments'
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
        "content_text": content_snippet
    })

embedded_json_str = json.dumps(embedded_docs)

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SDCounty HHSA Program Guide</title>
  <!-- Approved Tailwind script per generative_ui guidelines -->
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    .gradient-header {{
      background: linear-gradient(135deg, #0b2545 0%, #134074 50%, #001e3d 100%);
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
  </style>
</head>
<body class="bg-transparent text-[var(--foreground)] antialiased p-3 sm:p-5">

  <div class="max-w-5xl mx-auto bg-[var(--card)] text-[var(--foreground)] border border-[var(--border)] rounded-2xl shadow-xl overflow-hidden flex flex-col">
    
    <!-- Top Official Notice Bar -->
    <div class="bg-slate-900 text-slate-300 text-xs py-2 px-4 border-b border-slate-800 flex flex-wrap justify-between items-center gap-2">
      <div class="flex items-center gap-2">
        <svg class="w-4 h-4 text-amber-400 shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"></path>
        </svg>
        <span class="font-semibold text-slate-100">County of San Diego HHSA Policy Search Engine</span>
        <span class="text-slate-600">|</span>
        <span class="text-slate-400">{all_count} Deduplicated Policy Sections &amp; Handbooks</span>
      </div>
      <div class="flex items-center gap-3 text-xs">
        <a href="https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=542" target="_blank" class="hover:text-amber-300 underline transition">CalFresh Official (542) ↗</a>
        <a href="https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=448" target="_blank" class="hover:text-amber-300 underline transition">CalWORKs Official (448) ↗</a>
        <a href="https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=599" target="_blank" class="hover:text-amber-300 underline transition">Medi-Cal Official (599) ↗</a>
      </div>
    </div>

    <!-- Official Notice & Disclaimer Banner -->
    <div class="bg-amber-50 border-b border-amber-200 px-4 py-3 text-amber-900 text-xs flex items-start gap-3">
      <svg class="w-5 h-5 text-amber-600 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
      </svg>
      <div>
        <strong class="font-bold">Public Notice &amp; Disclaimer:</strong>
        This tool searches official County of San Diego Health and Human Services Agency (HHSA) Policy &amp; Procedure Guides. 
        It does not provide legal advice or make casework determinations. 
        To apply for benefits or report case changes, please visit 
        <a href="https://benefitscal.com/" target="_blank" class="text-blue-700 underline font-semibold hover:text-blue-900">BenefitsCal.com ↗</a> 
        or the 
        <a href="https://www.sandiegocounty.gov/hhsa/" target="_blank" class="text-blue-700 underline font-semibold hover:text-blue-900">County of San Diego HHSA Portal ↗</a>.
      </div>
    </div>

    <!-- Hero & Search Controls Section -->
    <div class="gradient-header text-white p-5 sm:p-7 border-b border-slate-700">
      <div class="max-w-4xl mx-auto text-center">
        <div class="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-500/20 text-blue-200 rounded-full text-xs font-medium border border-blue-400/30 mb-3">
          <svg class="w-3.5 h-3.5 text-blue-300" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"></path>
          </svg>
          Direct Policy Guide Search &amp; Grounded AI
        </div>
        <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight mb-2">SDCounty HHSA Program Guide</h1>
        <p class="text-slate-300 text-xs sm:text-sm max-w-xl mx-auto mb-5">
          Select any program to browse all policy chapters. Each chapter is an interactive dropdown to hide and unhide its subchapters with zero repeated sections.
        </p>

        <!-- Program Navigation Tabs -->
        <div class="bg-white/10 backdrop-blur-md p-1.5 rounded-xl border border-white/20 mb-4 flex flex-wrap items-center justify-between gap-2">
          <!-- Program Specific Buttons -->
          <div class="flex flex-wrap items-center gap-1.5 sm:gap-2">
            <button type="button" id="tab-CalFresh" onclick="switchProgram('CalFresh')" class="program-btn px-3.5 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 shadow-sm bg-blue-600 text-white cursor-pointer">
              <span>🌾 CalFresh (SNAP)</span>
              <span class="bg-blue-800 text-blue-100 text-xs px-1.5 py-0.5 rounded-full font-bold">{cf_count}</span>
            </button>
            <button type="button" id="tab-CalWORKs" onclick="switchProgram('CalWORKs')" class="program-btn px-3.5 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 bg-slate-800/60 text-slate-200 hover:bg-slate-700/80 cursor-pointer">
              <span>💼 CalWORKs (TANF)</span>
              <span class="bg-slate-700 text-slate-200 text-xs px-1.5 py-0.5 rounded-full font-bold">{cw_count}</span>
            </button>
            <button type="button" id="tab-Medi-Cal" onclick="switchProgram('Medi-Cal')" class="program-btn px-3.5 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 bg-slate-800/60 text-slate-200 hover:bg-slate-700/80 cursor-pointer">
              <span>🩺 Medi-Cal (Medicaid)</span>
              <span class="bg-slate-700 text-slate-200 text-xs px-1.5 py-0.5 rounded-full font-bold">{mc_count}</span>
            </button>
          </div>
          
          <!-- All Programs Button - Far right, highlighted in RED -->
          <div>
            <button type="button" id="tab-All" onclick="switchProgram('All')" class="program-btn px-4 py-2 rounded-lg text-xs font-extrabold transition flex items-center gap-1.5 bg-red-600 hover:bg-red-700 text-white shadow-md border-2 border-red-400 cursor-pointer">
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <span>All Programs (Search All)</span>
              <span class="bg-red-800 text-red-100 text-xs px-1.5 py-0.5 rounded-full font-bold">{all_count}</span>
            </button>
          </div>
        </div>

        <!-- Search Input Box & Submit Buttons -->
        <form id="searchForm" onsubmit="handleSearchSubmit(event)" class="flex flex-col sm:flex-row gap-2">
          <div class="relative flex-1">
            <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </div>
            <input type="text" id="searchInput" 
              placeholder="Searching ONLY CalFresh Guide (student eligibility, SUA, SAR 7, income limits)..." 
              class="w-full pl-10 pr-4 py-2.5 rounded-lg text-slate-900 bg-white border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs sm:text-sm font-medium shadow-inner">
          </div>
          <div class="flex gap-2 shrink-0">
            <button type="submit" name="searchMode" value="ask" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition shadow-sm cursor-pointer">
              <svg class="w-4 h-4 text-amber-300" fill="currentColor" viewBox="0 0 20 20">
                <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.477.859h4z"></path>
              </svg>
              <span>Ask Policy AI</span>
            </button>
            <button type="submit" name="searchMode" value="search" class="bg-slate-700 hover:bg-slate-800 text-white px-3.5 py-2.5 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition cursor-pointer">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>
              </svg>
              <span>Search Manual</span>
            </button>
            <button type="button" onclick="clearSearch()" class="bg-slate-800/80 hover:bg-slate-800 text-slate-300 px-2.5 py-2.5 rounded-lg text-xs font-semibold transition cursor-pointer" title="Clear Search">
              ✕
            </button>
          </div>
        </form>

        <!-- Deep BM25 Search Status Indicator -->
        <div class="flex items-center justify-between text-[11px] text-blue-200/90 mt-2 px-1">
          <div class="flex items-center gap-1.5">
            <span class="inline-block w-2 h-2 rounded-full bg-emerald-400"></span>
            <span><strong>BM25 Full-Text Engine:</strong> Searches 100% of PDF contents, regulations, tables & citations</span>
          </div>
          <div class="text-right text-blue-200/70 hidden sm:block">
            6,398 indexed section pages &bull; Exact excerpts
          </div>
        </div>

        <!-- Suggested Quick Topic Chips -->
        <div id="topicChipsContainer" class="flex flex-wrap items-center justify-center gap-1.5 mt-3">
          <!-- Populated dynamically -->
        </div>

      </div>
    </div>

    <!-- Main Content Body -->
    <div class="p-4 sm:p-6 flex-1 flex flex-col gap-5">
      
      <!-- VIEW 1: Manual Chapter & Section Dropdowns View (Default View) -->
      <div id="manualDropdownsView" class="flex flex-col gap-5">
        <!-- Section Catalog Header with Expand / Collapse All Controls -->
        <div class="flex flex-wrap items-center justify-between border-b border-slate-200 pb-3 gap-2">
          <div>
            <h3 id="listHeading" class="font-extrabold text-slate-800 text-sm sm:text-base">
              CalFresh Policy Manual Sections &amp; Chapters ({cf_count})
            </h3>
            <p id="resultMeta" class="text-xs text-slate-500 mt-0.5">
              Click any chapter or section dropdown below to view official regulations and subchapters.
            </p>
          </div>
          <div class="flex items-center gap-2">
            <button type="button" onclick="expandAllChapters()" class="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold px-2.5 py-1.5 rounded-lg border border-slate-300 transition flex items-center gap-1 cursor-pointer">
              <svg class="w-3.5 h-3.5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
              <span>Expand All</span>
            </button>
            <button type="button" onclick="collapseAllChapters()" class="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold px-2.5 py-1.5 rounded-lg border border-slate-300 transition flex items-center gap-1 cursor-pointer">
              <svg class="w-3.5 h-3.5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path></svg>
              <span>Collapse All</span>
            </button>
          </div>
        </div>

        <!-- List of Documents Grouped by Chapter Dropdowns -->
        <div id="documentsList" class="flex flex-col gap-3.5">
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
                <span id="searchResultScopeBadge" class="bg-blue-600 text-white text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider shrink-0">CalFresh</span>
                <h3 class="font-extrabold text-slate-900 text-sm sm:text-base truncate">
                  Search Results for: <span id="searchResultQueryText" class="text-blue-700">"..."</span>
                </h3>
              </div>
              <p id="searchResultCountText" class="text-xs text-slate-600 mt-0.5">
                Searching 100% of internal PDF text with BM25 engine...
              </p>
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

    <!-- Official Portal Footnotes -->
    <div class="bg-slate-100 border-t border-slate-200 p-4 text-xs text-slate-500 flex flex-wrap justify-between items-center gap-2">
      <div>
        SDCounty HHSA Program Guide • <strong>100% Original %PDF-1.7 Documents Locally Indexed</strong>
      </div>
      <div class="flex items-center gap-3">
        <a href="http://localhost:8000" target="_blank" class="hover:text-blue-600 font-semibold underline">Local Server: http://localhost:8000 ↗</a>
        <a href="https://benefitscal.com" target="_blank" class="hover:text-blue-600 underline">BenefitsCal.com ↗</a>
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
              <span id="pdfModalProgramBadge" class="text-[10px] uppercase tracking-wider font-extrabold px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-400/30 shrink-0">CalFresh</span>
              <h3 id="pdfModalTitle" class="text-xs sm:text-sm font-bold text-slate-100 truncate">Policy Document Title</h3>
            </div>
            <div id="pdfModalMeta" class="text-[11px] text-slate-400 truncate mt-0.5">Section • Official Document</div>
          </div>
        </div>

        <!-- Controls: Toggle Summary, Open in New Tab, Download, Close -->
        <div class="flex items-center gap-1.5 sm:gap-2 shrink-0">
          <button type="button" onclick="toggleModalSummary()" class="bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white px-2.5 py-1.5 rounded-lg text-xs font-semibold transition border border-slate-700 flex items-center gap-1 cursor-pointer" title="Toggle Quick Summary visibility">
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
      <div id="pdfModalSummaryBar" class="bg-blue-50/95 border-b border-blue-200 px-4 py-2 text-xs text-slate-800 flex items-start justify-between gap-3 shrink-0">
        <div class="flex items-start gap-2 min-w-0">
          <span class="font-bold text-blue-900 shrink-0 text-[11px] mt-0.5 flex items-center gap-1">
            <svg class="w-3.5 h-3.5 text-blue-600" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path></svg>
            Quick Summary:
          </span>
          <span id="pdfModalSummaryText" class="text-slate-700 line-clamp-2 leading-relaxed">Official policy summary...</span>
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
          <span class="text-[11px] text-slate-400 mt-1">Rendered via Browser Native PDF Viewer</span>
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
        placeholder: 'Searching ONLY CalFresh Guide (student eligibility, SUA, SAR 7, income limits)...',
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
        placeholder: 'Searching ONLY CalWORKs Guide (WTW participation hours, immediate need, property)...',
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
        placeholder: 'Searching ONLY Medi-Cal Guide (MAGI FPL, asset limit elimination, postpartum)...',
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
        placeholder: 'Search across all San Diego benefits guides (CalFresh, CalWORKs, Medi-Cal)...',
        chips: [
          {{ label: 'CalFresh Student Rules', query: 'CalFresh student eligibility' }},
          {{ label: 'CalWORKs WTW Hours', query: 'CalWORKs Welfare to Work hours' }},
          {{ label: 'Medi-Cal Asset Elimination', query: 'Medi-Cal asset limit elimination' }},
          {{ label: 'SAR 7 Reporting Requirements', query: 'Semi Annual Reporting SAR 7' }}
        ]
      }}
    }};

    function switchProgram(prog) {{
      activeProgram = prog;
      const meta = PROGRAM_METADATA[prog];

      // Update program button styles
      ['CalFresh', 'CalWORKs', 'Medi-Cal'].forEach(p => {{
        const btn = document.getElementById('tab-' + p);
        if (btn) {{
          if (p === prog) {{
            btn.className = 'program-btn px-3.5 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 shadow-sm bg-blue-600 text-white cursor-pointer';
          }} else {{
            btn.className = 'program-btn px-3.5 py-2 rounded-lg text-xs font-bold transition flex items-center gap-1.5 bg-slate-800/60 text-slate-200 hover:bg-slate-700/80 cursor-pointer';
          }}
        }}
      }});

      // Update All Programs button (Far right, highlighted in red)
      const allBtn = document.getElementById('tab-All');
      if (allBtn) {{
        if (prog === 'All') {{
          allBtn.className = 'program-btn px-4 py-2 rounded-lg text-xs font-extrabold transition flex items-center gap-1.5 bg-red-600 text-white shadow-lg border-2 border-white ring-2 ring-red-400 cursor-pointer';
        }} else {{
          allBtn.className = 'program-btn px-4 py-2 rounded-lg text-xs font-extrabold transition flex items-center gap-1.5 bg-red-600 hover:bg-red-700 text-white shadow-md border-2 border-red-400 cursor-pointer';
        }}
      }}

      // Update input placeholder
      const searchInp = document.getElementById('searchInput');
      if (searchInp) searchInp.placeholder = meta.placeholder;

      // Render suggested quick topic chips
      renderTopicChips(meta.chips);

      // Re-run search or display full program catalog
      const q = getSearchQuery();
      if (q) {{
        executeSearch(q, 'search');
      }} else {{
        cancelSearchToDropdowns();
      }}
    }}

    function renderTopicChips(chips) {{
      const container = document.getElementById('topicChipsContainer');
      if (!container) return;
      container.innerHTML = '';
      chips.forEach(c => {{
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'text-xs bg-white/10 hover:bg-white/20 text-blue-100 hover:text-white px-2.5 py-1 rounded-full border border-white/20 transition flex items-center gap-1 cursor-pointer';
        btn.innerHTML = '<span>💡</span> <span>' + escapeHtml(c.label) + '</span>';
        btn.onclick = () => {{
          setSearchQuery(c.query);
          handleSearchMode('ask');
        }};
        container.appendChild(btn);
      }});
    }}

    function clearSearch() {{
      cancelSearchToDropdowns();
    }}

    function handleSearchSubmit(e) {{
      e.preventDefault();
      const mode = (e.submitter && e.submitter.value) || 'search';
      handleSearchMode(mode);
    }}

    function handleSearchMode(mode) {{
      const q = getSearchQuery();
      if (!q) {{
        executeSearch('', 'list');
        return;
      }}
      executeSearch(q, mode);
    }}

    function highlightMatchedText(text, query) {{
      if (!text || !query) return escapeHtml(text || '');
      const words = query.toLowerCase().split(/\\s+/).filter(w => w.length > 2);
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

      const words = query.toLowerCase().split(/\\s+/).filter(Boolean);
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

    async function executeSearch(query, mode) {{
      const prog = activeProgram;
      const meta = PROGRAM_METADATA[prog];

      if (!query || !query.trim()) {{
        cancelSearchToDropdowns();
        return;
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
      if (countText) countText.textContent = 'Searching 100% of internal PDF text with BM25 engine...';

      if (mode === 'ask') {{
        showAIAnswerLoading();
        let aiData = null;
        try {{
          const resp = await fetch(LOCAL_SERVER_BASE + '/api/ask', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ question: query, program: prog }})
          }});
          if (resp.ok) {{
            aiData = await resp.json();
          }}
        }} catch (err) {{
          console.warn('Backend /api/ask unavailable, using client-side synthesis:', err);
        }}

        if (aiData && aiData.answer) {{
          renderAIAnswer(aiData.answer, aiData.sources || []);
        }} else {{
          synthesizeClientAnswer(query, prog);
        }}
      }} else {{
        const aiContainer = document.getElementById('aiAnswerContainer');
        if (aiContainer) aiContainer.classList.add('hidden');
      }}

      // 1. Full-Text BM25 Deep Search via Backend API when available
      let apiDocs = null;
      try {{
        const searchResp = await fetch(LOCAL_SERVER_BASE + '/api/search?q=' + encodeURIComponent(query) + '&program=' + encodeURIComponent(prog) + '&limit=150');
        if (searchResp.ok) {{
          const data = await searchResp.json();
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
        }}
      }} catch (err) {{
        console.log('Using client-side full-text search fallback:', err);
      }}

      // 2. Render matching documents in dedicated search results page
      const docs = apiDocs || filterDocs(query, prog);
      if (countText) {{
        countText.textContent = `${{docs.length}} matching official policy document${{docs.length === 1 ? '' : 's'}} (Ranked by BM25 Relevance)`;
      }}
      renderSearchResultsView(docs, query);
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
          const localPdf = resolveLocalPdfUrl(s.local_pdf_url, s.id);
          el.innerHTML = `
            <div class="mb-2">
              <div class="font-bold text-slate-800 line-clamp-1">${{escapeHtml(s.title)}}</div>
              <div class="mt-1.5 p-2 bg-blue-50/70 border border-blue-100 rounded text-xs text-slate-700 leading-relaxed">
                <span class="font-bold text-blue-900 block text-[11px] mb-0.5">Quick PDF Summary:</span>
                ${{escapeHtml(s.summary || s.snippet || '')}}
              </div>
            </div>
            <div class="flex items-center justify-between pt-1 border-t border-slate-100 text-xs">
              <span class="font-semibold text-blue-600">${{(s.programs || []).join(', ')}}</span>
              <div class="flex items-center gap-1.5">
                <button type="button" onclick="viewDocPdf('${{s.id}}')" class="bg-emerald-600 hover:bg-emerald-700 text-white px-2.5 py-1 rounded font-bold transition inline-flex items-center gap-1 shadow-2xs cursor-pointer">
                  <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/></svg>
                  <span>View in Page</span>
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
        `• **Quick Policy Summary**: ${{topMatch.summary || topMatch.snippet.slice(0, 300)}}\\n\\n` +
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
      
      if (summary && summary.trim()) {{
        summaryEl.textContent = summary;
        summaryBar.classList.remove('hidden');
      }} else {{
        summaryBar.classList.add('hidden');
      }}

      newTabBtn.href = pdfUrl;
      if (downloadBtn) {{
        downloadBtn.href = pdfUrl;
        downloadBtn.setAttribute('download', (section ? (section + ' - ') : '') + (title || 'document') + '.pdf');
      }}

      loading.classList.remove('hidden');
      iframe.src = pdfUrl;

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

    function toggleModalSummary() {{
      const summaryBar = document.getElementById('pdfModalSummaryBar');
      if (summaryBar) {{
        summaryBar.classList.toggle('hidden');
      }}
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
      const pdfUrl = resolveLocalPdfUrl(doc.local_pdf_url, doc.id);
      openPdfModal(pdfUrl, doc.title, (doc.programs || []).join(' / '), doc.summary || doc.snippet || '', doc.chapter || doc.id);
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

    // Interactive Dropdown Toggle Function for Each Chapter
    function toggleChapterDropdown(groupId) {{
      const content = document.getElementById('chapter-content-' + groupId);
      const chevron = document.getElementById('chapter-chevron-' + groupId);
      const headerBtn = document.getElementById('chapter-header-' + groupId);
      if (!content) return;

      const isHidden = content.classList.contains('hidden');
      if (isHidden) {{
        content.classList.remove('hidden');
        if (chevron) chevron.classList.add('rotate-180');
        if (headerBtn) {{
          headerBtn.classList.add('bg-blue-50/70', 'border-b', 'border-slate-200');
        }}
      }} else {{
        content.classList.add('hidden');
        if (chevron) chevron.classList.remove('rotate-180');
        if (headerBtn) {{
          headerBtn.classList.remove('bg-blue-50/70', 'border-b', 'border-slate-200');
        }}
      }}
    }}

    function expandAllChapters() {{
      document.querySelectorAll('.chapter-content-panel').forEach(el => el.classList.remove('hidden'));
      document.querySelectorAll('.chapter-chevron-icon').forEach(el => el.classList.add('rotate-180'));
      document.querySelectorAll('.chapter-header-btn').forEach(el => el.classList.add('bg-blue-50/70', 'border-b', 'border-slate-200'));
    }}

    function collapseAllChapters() {{
      document.querySelectorAll('.chapter-content-panel').forEach(el => el.classList.add('hidden'));
      document.querySelectorAll('.chapter-chevron-icon').forEach(el => el.classList.remove('rotate-180'));
      document.querySelectorAll('.chapter-header-btn').forEach(el => el.classList.remove('bg-blue-50/70', 'border-b', 'border-slate-200'));
    }}

    function createDocumentCard(doc, query) {{
      const card = document.createElement('div');
      card.className = 'border border-slate-200 hover:border-blue-400 rounded-lg p-3 sm:p-3.5 shadow-2xs hover:shadow-xs transition flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 bg-white';
      
      const progBadgeColor = doc.programs.includes('CalFresh') 
        ? 'bg-emerald-100 text-emerald-800 border-emerald-200' 
        : doc.programs.includes('CalWORKs') 
          ? 'bg-purple-100 text-purple-800 border-purple-200' 
          : 'bg-teal-100 text-teal-800 border-teal-200';

      const localPdfLink = resolveLocalPdfUrl(doc.local_pdf_url, doc.id);
      const revisionStr = doc.published_on ? doc.published_on.slice(0, 10) : 'Active';

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
          </div>
          
          <!-- Quick PDF Summary Everywhere -->
          <div class="my-2 p-2.5 bg-slate-50 border border-slate-200/90 rounded-lg text-xs text-slate-700 leading-relaxed shadow-2xs">
            <div class="flex items-center gap-1.5 text-blue-900 font-bold mb-1 text-[11px] tracking-wide">
              <svg class="w-3.5 h-3.5 text-blue-600 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path></svg>
              <span>Quick Policy Summary:</span>
            </div>
            <div class="text-slate-700 font-normal">
              ${{escapeHtml(doc.summary || doc.snippet || 'Official County of San Diego Health and Human Services Agency Policy Document.')}}
            </div>
          </div>

          <!-- Deep PDF Body Match (if query matched inside PDF) -->
          ${{doc.matched_excerpt ? `
            <div class="my-2 p-2.5 bg-amber-50/90 border border-amber-300 rounded-lg text-xs text-slate-800 leading-relaxed shadow-2xs">
              <div class="flex items-center justify-between mb-1.5 text-[11px]">
                <span class="font-bold text-amber-950 flex items-center gap-1.5">
                  <svg class="w-3.5 h-3.5 text-amber-700 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path></svg>
                  <span>Matched PDF Body Passage:</span>
                </span>
                <span class="bg-amber-200 text-amber-950 font-bold text-[10px] px-1.5 py-0.5 rounded border border-amber-300">
                  BM25 Score: ${{doc.score || 'Full Text Match'}}
                </span>
              </div>
              <div class="font-mono text-[11px] text-slate-800 bg-white/80 p-2 rounded border border-amber-200/80">
                ${{highlightMatchedText(doc.matched_excerpt, query)}}
              </div>
            </div>
          ` : ''}}

          <div class="flex items-center gap-3 text-xs text-slate-400 mt-1">
            <span>Section: <strong class="text-slate-600">${{escapeHtml(doc.section_num ? (doc.section_num + (doc.section_title ? (' • ' + doc.section_title) : '')) : (doc.chapter || doc.id))}}</strong></span>
            <span>•</span>
            <span>Revised: ${{revisionStr}}</span>
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0 w-full sm:w-auto justify-end pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100">
          <button type="button" onclick="viewDocPdf('${{doc.id}}')" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-3.5 py-2 rounded-lg transition inline-flex items-center gap-1.5 shadow-2xs cursor-pointer">
            <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/></svg>
            <span>View PDF in Page</span>
          </button>
          <a href="${{localPdfLink}}" target="_blank" class="bg-red-600 hover:bg-red-700 text-white text-xs font-bold px-2.5 py-2 rounded-lg transition inline-flex items-center gap-1 shadow-2xs" title="Open in new window or tab">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
            <span class="hidden md:inline">New Tab</span>
          </a>
        </div>
      `;
      return card;
    }}

    function renderDropdownsView(docs) {{
      const meta = PROGRAM_METADATA[activeProgram];
      const heading = document.getElementById('listHeading');
      if (heading) {{
        heading.innerText = `${{activeProgram === 'All' ? 'All County Benefits Policy Manual Sections & Chapters' : meta.title + ' Policy Manual Sections & Chapters'}} (${{docs.length}})`;
      }}

      const container = document.getElementById('documentsList');
      if (!container) return;
      container.innerHTML = '';

      // Group documents by Category / Chapter preserving ordering
      const groups = {{}};
      const groupOrders = {{}};
      const groupDescs = {{}};
      const groupIds = {{}};

      docs.forEach(doc => {{
        const cat = doc.category || 'General Sections';
        if (!groups[cat]) {{
          groups[cat] = [];
          groupOrders[cat] = doc.order || 50;
          groupDescs[cat] = doc.category_desc || 'County Policy and Procedure Sections';
          groupIds[cat] = doc.category_id || cat.replace(/[^a-zA-Z0-9]/g, '-').toLowerCase();
        }}
        groups[cat].push(doc);
      }});

      const sortedGroupNames = Object.keys(groups).sort((a, b) => groupOrders[a] - groupOrders[b]);

      // Render each Chapter as an interactive Dropdown Card
      sortedGroupNames.forEach((catName, groupIdx) => {{
        const groupDocs = groups[catName];
        const gId = groupIds[catName] || ('ch-' + groupIdx);
        const gDesc = groupDescs[catName];
        const isInitiallyOpen = (groupIdx === 0);

        const chapterCard = document.createElement('div');
        chapterCard.className = 'chapter-dropdown-card bg-white border border-slate-200/90 hover:border-slate-300 rounded-xl overflow-hidden shadow-2xs transition';

        // Dropdown Header Button
        const headerBtn = document.createElement('button');
        headerBtn.type = 'button';
        headerBtn.id = 'chapter-header-' + gId;
        headerBtn.className = `chapter-header-btn w-full flex items-center justify-between p-3.5 sm:p-4 text-left cursor-pointer transition select-none ${{
          isInitiallyOpen ? 'bg-blue-50/70 border-b border-slate-200' : 'bg-slate-50 hover:bg-slate-100'
        }}`;
        headerBtn.onclick = () => toggleChapterDropdown(gId);

        const cfMatch = catName.match(/^(63-\d+)\s+(.*)$/);
        const cwMatch = catName.match(/^([0-5]\d-\d{3}|69-\d{3}|70-\d{3})\s+(.*)$/);
        const mcMatch = catName.match(/^(ARTICLE\s+\d+)\s*[-–:]*\s*(.*)$/i);
        let titleBlock = '';
        if (cfMatch) {{
          titleBlock = `
            <div class="flex items-center gap-2">
              <span class="bg-emerald-700 text-white font-mono font-extrabold text-xs px-2.5 py-0.5 rounded shadow-2xs shrink-0">${{cfMatch[1]}}</span>
              <h4 class="font-extrabold text-slate-800 text-xs sm:text-sm tracking-tight truncate">${{escapeHtml(cfMatch[2])}}</h4>
            </div>
          `;
        }} else if (cwMatch) {{
          titleBlock = `
            <div class="flex items-center gap-2">
              <span class="bg-purple-700 text-white font-mono font-extrabold text-xs px-2.5 py-0.5 rounded shadow-2xs shrink-0">${{cwMatch[1]}}</span>
              <h4 class="font-extrabold text-slate-800 text-xs sm:text-sm tracking-tight truncate">${{escapeHtml(cwMatch[2])}}</h4>
            </div>
          `;
        }} else if (mcMatch) {{
          titleBlock = `
            <div class="flex items-center gap-2">
              <span class="bg-teal-700 text-white font-mono font-extrabold text-xs px-2.5 py-0.5 rounded shadow-2xs shrink-0">${{mcMatch[1]}}</span>
              <h4 class="font-extrabold text-slate-800 text-xs sm:text-sm tracking-tight truncate">${{escapeHtml(mcMatch[2])}}</h4>
            </div>
          `;
        }} else if (catName.includes('Special Notices')) {{
          titleBlock = `
            <div class="flex items-center gap-2">
              <span class="bg-amber-600 text-white font-mono font-extrabold text-[11px] px-2 py-0.5 rounded shadow-2xs shrink-0">NOTICES</span>
              <h4 class="font-extrabold text-slate-800 text-xs sm:text-sm tracking-tight truncate">${{escapeHtml(catName)}}</h4>
            </div>
          `;
        }} else {{
          titleBlock = `
            <div class="flex items-center gap-2">
              <h4 class="font-extrabold text-slate-800 text-xs sm:text-sm tracking-tight truncate">${{escapeHtml(catName)}}</h4>
            </div>
          `;
        }}

        headerBtn.innerHTML = `
          <div class="flex items-center gap-3 min-w-0 pr-2">
            <div class="w-8 h-8 rounded-lg ${{isInitiallyOpen ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700'}} flex items-center justify-center font-extrabold text-xs shrink-0 shadow-2xs">
              ${{groupIdx + 1}}
            </div>
            <div class="min-w-0">
              ${{titleBlock}}
              <p class="text-xs text-slate-500 mt-0.5 line-clamp-1">${{escapeHtml(gDesc)}}</p>
            </div>
          </div>
          <div class="flex items-center gap-2.5 shrink-0">
            <span class="bg-white border border-slate-200 text-slate-700 font-bold text-xs px-2.5 py-1 rounded-full shadow-2xs">
              ${{groupDocs.length}} ${{groupDocs.length === 1 ? 'subchapter' : 'subchapters'}}
            </span>
            <svg id="chapter-chevron-${{gId}}" class="chapter-chevron-icon chapter-chevron w-5 h-5 text-slate-400 ${{isInitiallyOpen ? 'rotate-180' : ''}}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
          </div>
        `;
        chapterCard.appendChild(headerBtn);

        // Subchapters / Sections Content Container
        const contentPanel = document.createElement('div');
        contentPanel.id = 'chapter-content-' + gId;
        contentPanel.className = `chapter-content-panel p-3 sm:p-4 flex flex-col gap-2.5 bg-slate-50/40 ${{isInitiallyOpen ? '' : 'hidden'}}`;

        groupDocs.forEach(doc => {{
          contentPanel.appendChild(createDocumentCard(doc, ''));
        }});

        chapterCard.appendChild(contentPanel);
        container.appendChild(chapterCard);
      }});
    }}

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
              <button type="button" onclick="switchProgram('All'); executeSearch('${{escapeHtml(query)}}', 'search')" class="bg-red-600 hover:bg-red-700 text-white font-bold px-4 py-2 rounded-lg transition shadow-xs cursor-pointer">
                Search All Programs
              </button>
            </div>
          </div>
        `;
        return;
      }}

      docs.forEach(doc => {{
        container.appendChild(createDocumentCard(doc, query));
      }});
    }}

    function cancelSearchToDropdowns() {{
      setSearchQuery('');
      const manualView = document.getElementById('manualDropdownsView');
      const searchView = document.getElementById('searchResultsPageView');
      const aiContainer = document.getElementById('aiAnswerContainer');

      if (searchView) searchView.classList.add('hidden');
      if (manualView) manualView.classList.remove('hidden');
      if (aiContainer) aiContainer.classList.add('hidden');

      // Refresh default dropdowns view
      const currentDocs = filterDocs('', activeProgram);
      renderDropdownsView(currentDocs);
    }}

    // Auto initialize with CalFresh on load
    document.addEventListener('DOMContentLoaded', () => {{
      switchProgram('CalFresh');
      const searchInp = document.getElementById('searchInput');
      if (searchInp) {{
        searchInp.addEventListener('input', (e) => {{
          if (!e.target.value.trim()) {{
            const searchView = document.getElementById('searchResultsPageView');
            if (searchView && !searchView.classList.contains('hidden')) {{
              cancelSearchToDropdowns();
            }}
          }}
        }});
      }}
    }});
  </script>
</body>
</html>"""

# Generate preview file for iframe / agent-embed
preview_html = html_template.replace('__SERVER_BASE__', 'http://localhost:8000')

with open(ARTIFACT_PATH, 'w', encoding='utf-8') as f:
    f.write(preview_html)

print(f"Generated {ARTIFACT_PATH} ({os.path.getsize(ARTIFACT_PATH)} bytes)")

# Generate templates/index.html for server.py
web_html = html_template.replace('__SERVER_BASE__', '')
with open(TEMPLATE_PATH, 'w', encoding='utf-8') as f:
    f.write(web_html)

print(f"Generated {TEMPLATE_PATH} ({os.path.getsize(TEMPLATE_PATH)} bytes)")
