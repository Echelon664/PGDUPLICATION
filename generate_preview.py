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
    # CalFresh
    'Chapter 63-100: Application Process & General Provisions': 'Household concept, application filing, expedited 3-day service, interviews, verification, and IRT',
    'Chapter 63-150: Students & Non-Financial Rules': 'Student 20-hr work exemptions, residency, citizenship, CFAP, SSN requirements, fraud, and Restaurant Meals Program (RMP)',
    'Chapter 63-200: Resources, Income & Deductions': 'Standard Utility Allowance (SUA), 20% earned income deduction, medical deductions, and shelter costs',
    'Chapter 63-270 / 63-300: SAR 7 & Recertification': 'Semi-Annual Reporting (SAR 7), IRT reporting, recertification timeframes, and SSI/SSP expansion',
    'Chapter 63-350: Case Administration & Pilots': 'Elderly Simplified Application Project (ESAP), confidentiality, inter-county transfers, and pilots',
    'Chapter 63-450 / 63-500: Claims, Fraud & Disaster': 'Overissuances, IPV penalties, Disaster CalFresh, and replacement benefits',
    'Chapter 63-600: Policy Questions & Answers': 'Official County eligibility, budgeting, deduction, and claim policy Q&A handbooks',
    'Chapter 63-900: Work Registration & ABAWD': 'CalFresh Employment & Training (CFET), work registration exemptions, and ABAWD rules',
    'Chapter 63-1100: Standards & Benefit Tables': 'Gross 130% FPL, Net 100% FPL, Maximum Allotments, and budgeting formulas',
    'Special Notices & Policy Updates': 'County Policy Bulletins, COLA notices, emergency directives, and annual adjustments',

    # CalWORKs
    'Chapter 10: Stage One Child Care': 'Child care duration, eligibility, assessment, transfers, and provider payments',
    'Chapter 10: Welfare-to-Work (WTW) & Employment': 'Core work participation (30/35 hrs), learning disabilities, subsidized employment, and supportive services',
    'Chapter 40: Application & General Requirements': 'Application filing, interviews, rights and responsibilities, and Immediate Need emergency cash ($200)',
    'Chapter 41: Age & Deprivation': 'Age rules, deprivation factors (unemployment, continued absence, incapacity, death)',
    'Chapter 42: Non-Financial & Property Limits': 'Residence, citizenship/noncitizen rules, vehicle exemptions, and property limitation thresholds',
    'Chapter 44: Budgeting, Income & MAP': 'Maximum Aid Payment (MAP) tables, income disregards, self-employment, and SAR 7 reporting',
    'Program Operations & Special Services': 'Case management, program exit, and specialized county supportive programs',
    'Special Notices & Policy Bulletins': 'COLA increases, state directives, and policy update notices',

    # Medi-Cal
    'MAGI Eligibility & Income Limits': 'Modified Adjusted Gross Income, 138% Federal Poverty Level thresholds, and Covered California coordination',
    'Property Rules & 2024 Asset Elimination': 'Complete elimination of asset/property test effective January 1, 2024, and vehicle rules',
    'Postpartum & Continuous Child Coverage': '12-month postpartum continuous coverage and continuous child eligibility for children under 5',
    'Citizenship & Full Scope Expansion': 'Full-scope Medi-Cal expansion for adults ages 26–49 regardless of immigration status',
    'Renewals, Ex Parte & Redeterminations': 'Automatic ex parte electronic renewals, redetermination packets, and disenrollment protections',
    'LTC, Waivers & Spousal Impoverishment': 'Long-Term Care, Home & Community-Based waivers, and spousal impoverishment caps',
    'Sections 01–05: Application & Initial Eligibility': 'County of responsibility, conditions of eligibility, hospital referrals, minor consent, immediate need',
    'Sections 06–10: Interviews & Verification': 'Interviews, identity verification, citizenship, noncitizen status, and residency',
    'Sections 11–15: Property & Treatment of Income': 'Income calculations, exempt income, child support, and treatment of property',
    'Sections 16–20: Special Coverage Groups & Waivers': 'Refugees, foster care, breast & cervical cancer treatment, and waiver programs',
    'Sections 21+: Case Maintenance & Administration': 'Case maintenance, inter-county transfers, confidentiality, and notices of action',
    'Special Notices & All County Letters': 'Statewide ACWDL letters, FPL updates, and emergency directives',
    'General Medi-Cal Eligibility & Administration': 'Administrative guidelines, hearings, confidentiality, and case records'
}

def categorize_doc(doc):
    title = doc.get('title', '')
    chapter = doc.get('chapter', '')
    programs = doc.get('programs', [])
    t = f"{title} {chapter}".lower()
    
    if 'CalFresh' in programs:
        if 'sn ' in t or 'special notice' in t:
            return 'Special Notices & Policy Updates', 'cf-sn', 99
        if '63-1101' in t or '63-1103' in t:
            return 'Chapter 63-1100: Standards & Benefit Tables', 'cf-63-1100', 90
        if '63-9' in t:
            return 'Chapter 63-900: Work Registration & ABAWD', 'cf-63-900', 80
        if '63-6' in t:
            return 'Chapter 63-600: Policy Questions & Answers', 'cf-63-600', 70
        if '63-45' in t or '63-5' in t:
            return 'Chapter 63-450 / 63-500: Claims, Fraud & Disaster', 'cf-63-450', 60
        if any(k in t for k in ['63-35', '63-36', '63-37', '63-38', '63-42']):
            return 'Chapter 63-350: Case Administration & Pilots', 'cf-63-350', 50
        if any(k in t for k in ['63-27', '63-28', '63-30', '63-32', '63-33', 'sar 7', 'recertification']):
            return 'Chapter 63-270 / 63-300: SAR 7 & Recertification', 'cf-63-270', 40
        if '63-2' in t:
            return 'Chapter 63-200: Resources, Income & Deductions', 'cf-63-200', 30
        if any(k in t for k in ['63-15', '63-16', 'student', 'citizenship', 'noncitizen', 'ssn', 'cfap']):
            return 'Chapter 63-150: Students & Non-Financial Rules', 'cf-63-150', 20
        return 'Chapter 63-100: Application Process & General Provisions', 'cf-63-100', 10

    elif 'CalWORKs' in programs:
        if 'sn ' in t or 'notice' in t:
            return 'Special Notices & Policy Bulletins', 'cw-sn', 99
        if any(k in t for k in ['child care', 'stage one', '10-010']):
            return 'Chapter 10: Stage One Child Care', 'cw-childcare', 15
        if any(k in t for k in ['welfare-to-work', 'wtw', 'work participation', '10-00', '10-02', '10-03', '10-05', '10-15', 'subsidized', 'community service', 'supportive']):
            return 'Chapter 10: Welfare-to-Work (WTW) & Employment', 'cw-wtw', 10
        if any(k in t for k in ['immediate need', 'application', 'rights', '40-']):
            return 'Chapter 40: Application & General Requirements', 'cw-40', 20
        if any(k in t for k in ['deprivation', 'age', '41-']):
            return 'Chapter 41: Age & Deprivation', 'cw-41', 30
        if any(k in t for k in ['residence', 'noncitizen', 'citizenship', 'property', 'resource', 'vehicle', '42-']):
            return 'Chapter 42: Non-Financial & Property Limits', 'cw-42', 40
        if any(k in t for k in ['income', 'budget', 'map', 'earned', 'unearned', 'sar 7', 'reporting', '44-']):
            return 'Chapter 44: Budgeting, Income & MAP', 'cw-44', 50
        return 'Program Operations & Special Services', 'cw-ops', 60

    else: # Medi-Cal
        if 'sn ' in t or 'acwdl' in t or 'bulletin' in t or 'special notice' in t:
            return 'Special Notices & All County Letters', 'mc-sn', 99
        if any(k in t for k in ['magi', 'fpl', 'modified adjusted']):
            return 'MAGI Eligibility & Income Limits', 'mc-magi', 10
        if any(k in t for k in ['asset', 'property', 'resource', 'elimination']):
            return 'Property Rules & 2024 Asset Elimination', 'mc-asset', 20
        if any(k in t for k in ['child', 'children', 'under 5', 'postpartum', 'pregnant']):
            return 'Postpartum & Continuous Child Coverage', 'mc-child', 30
        if any(k in t for k in ['citizenship', 'noncitizen', 'immigrant', 'undocumented', 'expansion']):
            return 'Citizenship & Full Scope Expansion', 'mc-citizen', 40
        if any(k in t for k in ['renewal', 'redetermination', 'ex parte', 'disenrollment']):
            return 'Renewals, Ex Parte & Redeterminations', 'mc-renew', 50
        if any(k in t for k in ['long term care', 'ltc', 'spousal', 'waiver', 'home and community']):
            return 'LTC, Waivers & Spousal Impoverishment', 'mc-ltc', 60
        m = re.search(r'Section[_\s]+(\d+)', title, re.IGNORECASE)
        if m:
            sec_num = int(m.group(1))
            if sec_num <= 5:
                return 'Sections 01–05: Application & Initial Eligibility', 'mc-sec-1-5', 70
            elif sec_num <= 10:
                return 'Sections 06–10: Interviews & Verification', 'mc-sec-6-10', 75
            elif sec_num <= 15:
                return 'Sections 11–15: Property & Treatment of Income', 'mc-sec-11-15', 80
            elif sec_num <= 20:
                return 'Sections 16–20: Special Coverage Groups & Waivers', 'mc-sec-16-20', 85
            else:
                return 'Sections 21+: Case Maintenance & Administration', 'mc-sec-high', 90
        return 'General Medi-Cal Eligibility & Administration', 'mc-general', 95

embedded_docs = []
for d in full_docs:
    cat_name, cat_id, cat_order = categorize_doc(d)
    content_snippet = d.get('content', '')[:1000].strip()
    cat_desc = CHAPTER_DESCRIPTIONS.get(cat_name, 'Official County Policy and Procedure Sections')
    embedded_docs.append({
        "id": d.get("id"),
        "title": d.get("title", ""),
        "chapter": d.get("chapter", ""),
        "programs": d.get("programs", []),
        "category": cat_name,
        "category_id": cat_id,
        "category_desc": cat_desc,
        "order": cat_order,
        "published_on": d.get("published_on", ""),
        "file_type": d.get("file_type", "PDF"),
        "local_pdf_url": d.get("local_pdf_url", ""),
        "official_url": d.get("official_url", ""),
        "summary": d.get("summary", ""),
        "snippet": content_snippet
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

        <!-- Suggested Quick Topic Chips -->
        <div id="topicChipsContainer" class="flex flex-wrap items-center justify-center gap-1.5 mt-3">
          <!-- Populated dynamically -->
        </div>

      </div>
    </div>

    <!-- Main Content Body -->
    <div class="p-4 sm:p-6 flex-1 flex flex-col gap-5">
      
      <!-- AI Answer Container -->
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

      <!-- Section Catalog & Search Results Header with Expand / Collapse All Controls -->
      <div class="flex flex-wrap items-center justify-between border-b border-slate-200 pb-3 gap-2">
        <div>
          <h3 id="listHeading" class="font-extrabold text-slate-800 text-sm sm:text-base">
            CalFresh Policy Manual Sections &amp; Chapters ({cf_count})
          </h3>
          <p id="resultMeta" class="text-xs text-slate-500 mt-0.5">
            Click any chapter dropdown below to hide or unhide its subchapters. Zero repeated sections.
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
        <!-- Populated dynamically -->
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
        folder: 'Folder 599 (Policy Articles)',
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

      // Reset AI answer box
      const aiContainer = document.getElementById('aiAnswerContainer');
      if (aiContainer) aiContainer.classList.add('hidden');

      // Re-run search or display full program catalog
      const q = getSearchQuery();
      executeSearch(q, q ? 'search' : 'list');
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
      setSearchQuery('');
      const aiContainer = document.getElementById('aiAnswerContainer');
      if (aiContainer) aiContainer.classList.add('hidden');
      executeSearch('', 'list');
    }}

    function handleSearchSubmit(e) {{
      e.preventDefault();
      const mode = (e.submitter && e.submitter.value) || 'ask';
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

    function filterDocs(query, prog) {{
      let filtered = EMBEDDED_DOCS;
      if (prog !== 'All') {{
        filtered = filtered.filter(d => (d.programs || []).includes(prog));
      }}
      if (!query) return filtered;

      const words = query.toLowerCase().split(/\\s+/).filter(Boolean);
      return filtered.filter(d => {{
        const title = (d.title || '').toLowerCase();
        const chapter = (d.chapter || '').toLowerCase();
        const category = (d.category || '').toLowerCase();
        const summary = (d.summary || '').toLowerCase();
        const snippet = (d.snippet || '').toLowerCase();
        return words.some(w => title.includes(w) || chapter.includes(w) || category.includes(w) || summary.includes(w) || snippet.includes(w));
      }}).sort((a, b) => {{
        const aTitle = words.filter(w => a.title.toLowerCase().includes(w)).length;
        const bTitle = words.filter(w => b.title.toLowerCase().includes(w)).length;
        return bTitle - aTitle;
      }});
    }}

    async function executeSearch(query, mode) {{
      const prog = activeProgram;
      const meta = PROGRAM_METADATA[prog];

      if (mode === 'ask' && query) {{
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

      // Render matching documents grouped by chapter dropdowns
      const docs = filterDocs(query, prog);
      renderDocumentsList(docs, query);
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
              <a href="${{localPdf}}" target="_blank" class="bg-red-600 hover:bg-red-700 text-white px-2.5 py-1 rounded font-bold transition inline-flex items-center gap-1 shadow-2xs">
                <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"></path></svg>
                <span>Open Whole PDF</span>
              </a>
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

    function renderDocumentsList(docs, query) {{
      const meta = PROGRAM_METADATA[activeProgram];
      const heading = document.getElementById('listHeading');
      
      if (query) {{
        heading.innerText = `Search Results: "${{query}}" in ${{activeProgram === 'All' ? 'All Programs' : meta.title}} (${{docs.length}} found)`;
      }} else {{
        heading.innerText = `${{activeProgram === 'All' ? 'All County Benefits Policy Manual Sections & Chapters' : meta.title + ' Policy Manual Sections & Chapters'}} (${{docs.length}})`;
      }}

      const container = document.getElementById('documentsList');
      container.innerHTML = '';

      if (docs.length === 0) {{
        container.innerHTML = `
          <div class="bg-amber-50 border border-amber-200 rounded-xl p-6 text-center text-amber-900 text-xs">
            <p class="font-bold text-sm mb-1">No matching documents found in ${{meta.title}}</p>
            <p class="text-slate-600 mb-3">No sections matched "${{escapeHtml(query)}}" inside this specific program guide.</p>
            <button type="button" onclick="switchProgram('All')" class="bg-red-600 hover:bg-red-700 text-white font-bold px-3 py-1.5 rounded-lg transition cursor-pointer">
              Search in All Programs ({all_count} Documents)
            </button>
          </div>
        `;
        return;
      }}

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

        // Should this dropdown be expanded initially?
        // Expand if searching, or expand the first chapter by default
        const isInitiallyOpen = (Boolean(query) || groupIdx === 0);

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

        headerBtn.innerHTML = `
          <div class="flex items-center gap-3 min-w-0 pr-2">
            <div class="w-8 h-8 rounded-lg ${{isInitiallyOpen ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700'}} flex items-center justify-center font-extrabold text-xs shrink-0 shadow-2xs">
              ${{groupIdx + 1}}
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <h4 class="font-extrabold text-slate-800 text-xs sm:text-sm tracking-tight truncate">${{escapeHtml(catName)}}</h4>
              </div>
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

        // Subchapters / Sections Content Container (Hidden / Unhidden by Dropdown)
        const contentPanel = document.createElement('div');
        contentPanel.id = 'chapter-content-' + gId;
        contentPanel.className = `chapter-content-panel p-3 sm:p-4 flex flex-col gap-2.5 bg-slate-50/40 ${{isInitiallyOpen ? '' : 'hidden'}}`;

        groupDocs.forEach(doc => {{
          const card = document.createElement('div');
          card.className = 'border border-slate-200 hover:border-blue-400 rounded-lg p-3 sm:p-3.5 shadow-2xs hover:shadow-xs transition flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 bg-white';
          
          const progBadgeColor = doc.programs.includes('CalFresh') 
            ? 'bg-emerald-100 text-emerald-800 border-emerald-200' 
            : doc.programs.includes('CalWORKs') 
              ? 'bg-purple-100 text-purple-800 border-purple-200' 
              : 'bg-sky-100 text-sky-800 border-sky-200';

          const localPdfLink = resolveLocalPdfUrl(doc.local_pdf_url, doc.id);
          const revisionStr = doc.published_on ? doc.published_on.slice(0, 10) : 'Active';

          card.innerHTML = `
            <div class="flex-1 min-w-0">
              <div class="flex flex-wrap items-center gap-2 mb-1.5">
                <span class="px-2 py-0.5 rounded text-xs font-bold border ${{progBadgeColor}}">${{(doc.programs || []).join(' / ')}}</span>
                <a href="${{localPdfLink}}" target="_blank" class="font-bold text-slate-800 text-xs sm:text-sm hover:text-blue-600 transition inline-flex items-center gap-1">
                  <span>${{escapeHtml(doc.title)}}</span>
                  <svg class="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                </a>
                <span class="text-xs bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-mono font-medium">Original PDF</span>
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

              <div class="flex items-center gap-3 text-xs text-slate-400 mt-1">
                <span>Section: <strong class="text-slate-600">${{escapeHtml(doc.chapter || doc.id)}}</strong></span>
                <span>•</span>
                <span>Revised: ${{revisionStr}}</span>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0 w-full sm:w-auto justify-end pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100">
              <a href="${{localPdfLink}}" target="_blank" class="bg-red-600 hover:bg-red-700 text-white text-xs font-bold px-3.5 py-2 rounded-lg transition inline-flex items-center gap-1.5 shadow-2xs">
                <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"></path></svg>
                <span>Open Whole PDF</span>
              </a>
            </div>
          `;
          contentPanel.appendChild(card);
        }});

        chapterCard.appendChild(contentPanel);
        container.appendChild(chapterCard);
      }});
    }}

    // Auto initialize with CalFresh on load
    document.addEventListener('DOMContentLoaded', () => {{
      switchProgram('CalFresh');
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
