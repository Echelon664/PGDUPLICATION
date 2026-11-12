import json
import os
from pdf_utils import generate_multipage_pdf

DOCS = [
  # --- CALFRESH (Folder 542) ---
  {
    "id": "63-100",
    "title": "Chapter 63-100: CalFresh Application Process & Expedited Service",
    "programs": ["CalFresh"],
    "published_on": "2024-10-01T00:00:00Z",
    "file_type": "PDF",
    "local_pdf_url": "/pdfs/63-100.pdf",
    "official_url": "https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=542",
    "sections": [
      {
        "heading": "1. Policy Background & Program Scope",
        "text": "The CalFresh Program provides monthly food assistance benefits to low-income individuals and families. The County of San Diego Health and Human Services Agency (HHSA) administers CalFresh locally under CDSS MPP Chapter 63-100. Applications can be submitted online via BenefitsCal.com, in person at Family Resource Centers, by telephone, or by mail."
      },
      {
        "heading": "2. Filing of Applications & 30-Day Processing",
        "text": "An application is officially filed on the date it is received by the county with applicant name, address, and signature. Standard applications must be processed within thirty (30) calendar days. An interactive eligibility interview is required prior to approval. Telephonic signatures are legally binding."
      },
      {
        "heading": "3. Expedited Service Mandatory Standards (3 Calendar Days)",
        "text": "Households qualifying for Expedited Service must receive benefits within three (3) calendar days. Criteria: 1) Gross monthly income under $150 and liquid resources under $100; 2) Combined monthly income and resources less than monthly rent/mortgage and utility expenses; 3) Destitute migrant/seasonal farmworker household with resources under $100. Identity is the ONLY mandatory verification prior to expedited issuance."
      },
      {
        "heading": "4. Authorized Representatives & Restaurant Meals Program (RMP)",
        "text": "Households may designate an authorized representative in writing to apply for and access benefits. Homeless households are eligible to use CalFresh EBT at participating restaurants under the San Diego County Restaurant Meals Program (RMP)."
      },
      {
        "heading": "5. Legal Citations & Regulatory Authorities",
        "text": "CDSS MPP Sections 63-300, 63-301; 7 CFR § 273.2; All County Letter (ACL) 23-45."
      }
    ]
  },
  {
    "id": "63-150",
    "title": "Chapter 63-150: Non-Financial Criteria - Student Eligibility Rules & Exemptions",
    "programs": ["CalFresh"],
    "published_on": "2024-10-01T00:00:00Z",
    "file_type": "PDF",
    "local_pdf_url": "/pdfs/63-150.pdf",
    "official_url": "https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=542",
    "sections": [
      {
        "heading": "1. Student Rule Overview & Definitions",
        "text": "Under federal and California state regulations (MPP 63-406), an individual enrolled at least half-time in an institution of higher education is considered a student and is ineligible for CalFresh unless meeting a recognized student exemption. Enrollment extends through normal vacation periods until graduation or formal withdrawal."
      },
      {
        "heading": "2. Approved Student Exemptions Checklist",
        "text": "A student meets an exemption if they satisfy ANY ONE of the following:\n• Employment: Employed for an average of at least 20 hours per week in paid employment, or earning federal minimum wage multiplied by 20 hours.\n• Work-Study: Approved for and participating in a state or federally financed work-study program.\n• Dependent Care: Caring for a dependent household member under age 6, or age 6-11 without adequate child care.\n• Single Parent: Single parent enrolled full-time caring for a child under age 12.\n• Welfare-to-Work: Participating in a CalWORKs Welfare-to-Work (WTW) assignment.\n• LPIE: Enrolled in an approved certificate, CTE, EOPS, Puente, or campus support program."
      },
      {
        "heading": "3. Citizenship and Immigrant Eligibility Standards",
        "text": "U.S. citizens and qualified non-citizens are eligible for federal CalFresh. Qualified non-citizens include Lawful Permanent Residents (LPRs) with 5 years of status or 40 work quarters, refugees, asylees, T-visa and U-visa holders. Non-citizens who do not qualify for federal SNAP due to immigration status may qualify for the California Food Assistance Program (CFAP)."
      },
      {
        "heading": "4. Social Security Numbers & County Residency",
        "text": "Each household member applying for CalFresh must provide or apply for an SSN. Non-applicants (such as undocumented parents applying on behalf of citizen children) are not required to provide an SSN. Applicants must reside in San Diego County."
      },
      {
        "heading": "5. Statutory References",
        "text": "7 CFR § 273.5; CDSS MPP § 63-406; California Welfare & Institutions Code § 18901.11; ACL 22-83."
      }
    ]
  },
  {
    "id": "63-230",
    "title": "Chapter 63-230: Income Deductions, Budgeting & Standard Utility Allowances (SUA)",
    "programs": ["CalFresh"],
    "published_on": "2024-10-01T00:00:00Z",
    "file_type": "PDF",
    "local_pdf_url": "/pdfs/63-230.pdf",
    "official_url": "https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=542",
    "sections": [
      {
        "heading": "1. Gross vs. Net Income Tests",
        "text": "Under Modified Categorical Eligibility (MCE), households without an elderly or disabled member must meet the Gross Income limit of 200% FPL. Households with an elderly (60+) or disabled member are exempt from the gross income test and are evaluated only against the 100% FPL Net Income limit."
      },
      {
        "heading": "2. Mandatory Income Deductions Schedule",
        "text": "Deductions subtracted from gross income in order:\n1. Standard Deduction: Universal deduction based on household size (1-3 persons: $200; 4 persons: $211; 5 persons: $247; 6+ persons: $283).\n2. Earned Income Deduction: 20% deduction applied to all gross earned wages.\n3. Excess Medical Deduction: For elderly (60+) or disabled individuals, verified medical costs exceeding $35/month are fully deductible.\n4. Dependent Care Deduction: Actual necessary child or adult dependent care expenses."
      },
      {
        "heading": "3. Shelter Deduction & Standard Utility Allowances (SUA)",
        "text": "The shelter deduction equals the amount by which total monthly shelter costs plus utility allowances exceed 50% of net income after all prior deductions.\n• Standard Utility Allowance (SUA): $596/month, applicable when heating or cooling costs are incurred.\n• Limited Utility Allowance (LUA): $162/month for at least two non-heating utilities.\n• Telephone Utility Allowance (TUA): $19/month for telephone expenses."
      },
      {
        "heading": "4. Benefit Calculation Formula",
        "text": "Monthly allotment = Maximum Allotment for Household Size minus 30% of Net Countable Monthly Income. Minimum monthly allotment for 1-2 person households is $23."
      },
      {
        "heading": "5. Legal Authority",
        "text": "CDSS MPP § 63-502.3; 7 CFR § 273.9; All County Information Notice (ACIN) I-45-24."
      }
    ]
  },
  {
    "id": "63-504",
    "title": "Chapter 63-504: Semi-Annual Reporting (SAR 7) & Income Reporting Threshold (IRT)",
    "programs": ["CalFresh"],
    "published_on": "2024-10-01T00:00:00Z",
    "file_type": "PDF",
    "local_pdf_url": "/pdfs/63-504.pdf",
    "official_url": "https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=542",
    "sections": [
      {
        "heading": "1. Periodic Reporting Framework (Semi-Annual)",
        "text": "Households are certified for 12 months. In the 6th month, households must submit form SAR 7 (Eligibility Status Report) along with proof of income for the designated data month."
      },
      {
        "heading": "2. Mandatory Mid-Period Reporting & The IRT Rule",
        "text": "Households must report within ten (10) calendar days whenever their total gross monthly income exceeds their assigned Income Reporting Threshold (IRT), set at 130% FPL for the certified household size."
      },
      {
        "heading": "3. Discontinuance & Restorations",
        "text": "If a household fails to submit SAR 7 by the extended deadline, benefits terminate at month end. If submitted within the 30-day restoration period following discontinuance, benefits are restored without a new application."
      },
      {
        "heading": "4. Legal Authorities",
        "text": "CDSS MPP § 63-504; Welfare & Institutions Code § 18910; ACL 23-88."
      }
    ]
  },
  {
    "id": "63-1100",
    "title": "Chapter 63-1100: Handbook - Allotments, Deductions & Federal Poverty Tables",
    "programs": ["CalFresh"],
    "published_on": "2024-10-01T00:00:00Z",
    "file_type": "PDF",
    "local_pdf_url": "/pdfs/63-1100.pdf",
    "official_url": "https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=542",
    "sections": [
      {
        "heading": "1. Maximum Monthly CalFresh Allotments",
        "text": "Effective October 1 (Federal COLA Update):\n• 1 Person: $292\n• 2 Persons: $536\n• 3 Persons: $768\n• 4 Persons: $975\n• 5 Persons: $1,158\n• 6 Persons: $1,390\n• 7 Persons: $1,536\n• 8 Persons: $1,756\n• Each additional person: +$220\nMinimum monthly benefit for 1-2 person households: $23."
      },
      {
        "heading": "2. Federal Poverty Level (FPL) Income Guidelines",
        "text": "Gross monthly income limit (200% FPL under MCE):\n• 1 Person: $2,510\n• 2 Persons: $3,408\n• 3 Persons: $4,304\n• 4 Persons: $5,200\n• 5 Persons: $6,098\nNet monthly income limit (100% FPL):\n• 1 Person: $1,255\n• 2 Persons: $1,704\n• 3 Persons: $2,152\n• 4 Persons: $2,600."
      },
      {
        "heading": "3. Maximum Shelter Deduction Cap",
        "text": "The maximum shelter deduction cap is $672 for households without elderly or disabled members. Households with an elderly or disabled member have no cap on allowable shelter deductions."
      }
    ]
  },

  # --- CALWORKS (Folder 448) ---
  {
    "id": "40-100",
    "title": "Chapter 40-100: CalWORKs Application Process & Immediate Need Aid",
    "programs": ["CalWORKs"],
    "published_on": "2024-05-01T00:00:00Z",
    "file_type": "PDF",
    "local_pdf_url": "/pdfs/40-100.pdf",
    "official_url": "https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=448",
    "sections": [
      {
        "heading": "1. Program Purpose & Intake Procedures",
        "text": "CalWORKs provides temporary financial assistance and employment services to families with minor children where parental support is interrupted by absence, disability, unemployment, or death. Standard applications must be determined within 45 calendar days."
      },
      {
        "heading": "2. Immediate Need Emergency Payments",
        "text": "Applicants facing an emergency situation (imminent eviction, lack of shelter, food crisis) with liquid resources under $100 may receive an Immediate Need payment of up to $200 within 1 business day of application while full eligibility verification is pending."
      },
      {
        "heading": "3. Diversion Services",
        "text": "Applicants with a short-term financial barrier who have immediate prospect of employment may be offered a one-time lump-sum Diversion payment instead of ongoing cash aid, avoiding CalWORKs time clocks."
      }
    ]
  },
  {
    "id": "42-100",
    "title": "Chapter 42-100: Welfare-to-Work (WTW) Participation, Activities & Sanctions",
    "programs": ["CalWORKs"],
    "published_on": "2024-05-15T00:00:00Z",
    "file_type": "PDF",
    "local_pdf_url": "/pdfs/42-100.pdf",
    "official_url": "https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=448",
    "sections": [
      {
        "heading": "1. Welfare-to-Work Mandate & Supportive Services",
        "text": "CalWORKs non-exempt adults must participate in Welfare-to-Work (WTW) activities. Guaranteed supportive services include paid child care, transportation reimbursements, work uniforms, and educational materials."
      },
      {
        "heading": "2. Hourly Participation Standards",
        "text": "• Single-Parent Household with child under 6: Minimum 20 hours per week.\n• Single-Parent Household with child 6+: Minimum 30 hours per week (at least 20 core hours).\n• Two-Parent Households: Combined minimum 35 hours per week (at least 30 core hours).\nCore activities include employment, vocational education, and work experience."
      },
      {
        "heading": "3. Exemption Categories",
        "text": "Exemptions include documented medical disability (Form CW 61), age 60+, caretaker of an incapacitated family member, or a parent caring for a child under 6 months."
      },
      {
        "heading": "4. Non-Compliance & Sanctions",
        "text": "Non-compliance without good cause results in a sanction that removes ONLY the adult's portion of the cash grant; children's cash aid and CalFresh benefits continue uninterrupted."
      }
    ]
  },
  {
    "id": "42-200",
    "title": "Chapter 42-200: CalWORKs Property and Resource Limitations",
    "programs": ["CalWORKs"],
    "published_on": "2024-05-15T00:00:00Z",
    "file_type": "PDF",
    "local_pdf_url": "/pdfs/42-200.pdf",
    "official_url": "https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=448",
    "sections": [
      {
        "heading": "1. Non-Exempt Property Limits",
        "text": "To qualify for CalWORKs, a family's non-exempt resources cannot exceed $11,634 (or $15,873 if the assistance unit includes an individual age 60 or older or disabled)."
      },
      {
        "heading": "2. Exempt Resources & Vehicle Exclusions",
        "text": "The primary home is completely exempt. One motor vehicle per licensed driver used for transportation or work is excluded up to equity limitations. Household goods and personal effects are fully exempt."
      }
    ]
  },
  {
    "id": "44-300",
    "title": "Chapter 44-300: Maximum Aid Payment (MAP) Standards & Income Disregards",
    "programs": ["CalWORKs"],
    "published_on": "2024-10-01T00:00:00Z",
    "file_type": "PDF",
    "local_pdf_url": "/pdfs/44-300.pdf",
    "official_url": "https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=448",
    "sections": [
      {
        "heading": "1. Region 1 MAP Payment Standards",
        "text": "San Diego County is in Region 1. Monthly cash aid is determined by comparing net countable income against the MAP standard for the Assistance Unit (AU) size."
      },
      {
        "heading": "2. $450 + 50% Earned Income Disregard",
        "text": "To encourage employment, the first $450 of gross monthly earnings is disregarded, plus 50% of any remaining earned wages before calculating the cash grant."
      }
    ]
  },

  # --- MEDI-CAL (Folder 599) ---
  {
    "id": "mc-art-02",
    "title": "Article 02: Medi-Cal Modified Adjusted Gross Income (MAGI) Eligibility",
    "programs": ["Medi-Cal"],
    "published_on": "2024-01-01T00:00:00Z",
    "file_type": "PDF",
    "local_pdf_url": "/pdfs/mc-art-02.pdf",
    "official_url": "https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=599",
    "sections": [
      {
        "heading": "1. Affordable Care Act & MAGI Methodology",
        "text": "Medi-Cal eligibility for children, pregnant individuals, and non-elderly adults is determined using Modified Adjusted Gross Income (MAGI) rules aligned with federal tax filing methodologies."
      },
      {
        "heading": "2. Federal Poverty Level (FPL) Income Standards",
        "text": "• Adults 19-64: Up to 138% FPL (inclusive of 5% disregard).\n• Pregnant Individuals: Full-scope coverage up to 213% FPL.\n• Infants (under 1 year): Up to 213% FPL.\n• Children 1-18: Up to 266% FPL."
      }
    ]
  },
  {
    "id": "mc-art-05",
    "title": "Article 05: Medi-Cal Asset Limit Elimination Guidelines (AB 133)",
    "programs": ["Medi-Cal"],
    "published_on": "2024-01-01T00:00:00Z",
    "file_type": "PDF",
    "local_pdf_url": "/pdfs/mc-art-05.pdf",
    "official_url": "https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=599",
    "sections": [
      {
        "heading": "1. Complete Elimination of Asset Limits",
        "text": "Effective January 1, 2024, California has completely eliminated asset and resource limits for all Medi-Cal programs across the state. This change applies to MAGI as well as Non-MAGI categories (individuals age 65+, blind, disabled, and Long-Term Care)."
      },
      {
        "heading": "2. Caseworker Verification Rules",
        "text": "County staff are strictly prohibited from requesting, verifying, or counting savings accounts, retirement funds, vehicles, real estate, or other personal assets when determining Medi-Cal eligibility."
      }
    ]
  },
  {
    "id": "mc-art-09",
    "title": "Article 09: Continuous Coverage for Children & Postpartum Individuals",
    "programs": ["Medi-Cal"],
    "published_on": "2024-01-01T00:00:00Z",
    "file_type": "PDF",
    "local_pdf_url": "/pdfs/mc-art-09.pdf",
    "official_url": "https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=599",
    "sections": [
      {
        "heading": "1. Continuous Child Eligibility (Under Age 5)",
        "text": "Children enrolled in Medi-Cal under age 5 receive continuous, uninterrupted coverage until their 5th birthday regardless of family income changes."
      },
      {
        "heading": "2. 12-Month Postpartum Coverage Guarantee",
        "text": "Postpartum individuals receive 12 months of continuous full-scope Medi-Cal coverage following the end of their pregnancy, ensuring unbroken access to medical care."
      }
    ]
  }
]

# Write updated documents.json
docs_json = []
for d in DOCS:
    full_text = "\n\n".join([f"{s['heading']}\n{s['text']}" for s in d["sections"]])
    docs_json.append({
        "id": d["id"],
        "title": d["title"],
        "programs": d["programs"],
        "published_on": d["published_on"],
        "file_type": "PDF",
        "local_pdf_url": d["local_pdf_url"],
        "official_url": d["official_url"],
        "content": full_text,
        "sections": d["sections"]
    })

data_dir = "/Users/echelon619/.gemini/antigravity/scratch/sd-benefits-search/data"
with open(os.path.join(data_dir, "documents.json"), "w") as f:
    json.dump(docs_json, f, indent=2)

# Generate multi-page PDFs
pdf_dir = os.path.join(data_dir, "pdfs")
for d in DOCS:
    out = os.path.join(pdf_dir, f"{d['id']}.pdf")
    generate_multipage_pdf(d["title"], d["programs"], d["published_on"], d["sections"], out)
    print(f"Generated: {out} ({os.path.getsize(out)} bytes)")

print(f"[✓] Total multi-page local PDFs generated: {len(DOCS)}")
