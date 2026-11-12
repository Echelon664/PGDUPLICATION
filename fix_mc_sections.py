#!/usr/bin/env python3
import json

DOCS_PATH = "/Users/echelon619/.gemini/antigravity/scratch/sd-benefits-search/data/documents.json"

with open(DOCS_PATH, "r") as f:
    docs = json.load(f)

MC_REAL_FIXES = {
    "mc-335": "Governs confidential Minor Consent services, enabling minors to receive sensitive outpatient health care services (sexual health, mental health, substance use) without parental disclosure or consent.",
    "mc-336": "Details Immediate Medical Need (IMN) processing, authorizing same-day or expedited Medi-Cal eligibility verification and card issuance for applicants requiring urgent medical care.",
    "mc-337": "Outlines intake and annual interview requirements, telephone interview options, and customer communication accommodations under Medi-Cal regulations.",
    "mc-338": "Establishes mandatory verification and documentation standards for identity, residency, income, and immigration status, prioritizing electronic verification.",
    "mc-339": "Details California residency requirements, physical presence rules, intent to reside standards, and accommodations for homeless or migrant individuals.",
    "mc-340": "Governs diligent search procedures required of caseworkers to locate lost contact information and missing beneficiaries before taking adverse case actions.",
    "mc-341": "Details the Child Health and Disability Prevention (CHDP) program, preventive health screening schedules, and referral coordination for eligible children.",
    "mc-342": "Details mandatory Social Security Number (SSN) disclosure rules, verification protocols, and non-citizen exemptions for state-funded Medi-Cal programs.",
    "mc-343": "Governs the treatment of unconditionally available income (such as pensions, annuities, and disability benefits) that an applicant has a legal right to receive.",
    "mc-344": "Establishes caseworker standards and timeliness requirements for denying or discontinuing Medi-Cal applications and ongoing cases.",
    "mc-345": "Details annual Medi-Cal eligibility renewals, automated ex parte reviews using electronic data sources, and yellow packet renewal processing.",
    "mc-346": "Governs Inter-Program and Intra-Program case transfers, transitioning beneficiaries between aid codes and Medi-Cal programs without interruption of coverage.",
    "mc-347": "Establishes requirements for issuing timely and adequate Notice of Action (NOA), including 10-day advance notice standards for reductions or terminations.",
    "mc-348": "Outlines Medical Support Enforcement Program requirements, custodial parent cooperation with DCSS, and good cause exemptions.",
    "mc-349": "Governs eligibility processing for applicants residing in Long-Term Care (LTC) facilities or incompetent individuals requiring an authorized representative.",
    "mc-350": "Details the Accelerated Enrollment (AE) program providing immediate, temporary full-scope Medi-Cal coverage to eligible children pending full application processing.",
    "mc-351": "Establishes documented good cause criteria excusing failure to complete renewals or submit required verification within standard timelines.",
    "mc-352": "Outlines the mandatory Medi-Cal program hierarchy, directing caseworkers to evaluate applicants for zero-share-of-cost programs prior to share-of-cost programs.",
    "mc-353": "Details IRS Form 1095-B reporting for beneficiaries receiving Minimum Essential Coverage (MEC) through Medi-Cal.",
    "mc-354": "Establishes core Medi-Cal coverage categories, distinguishing MAGI, Non-MAGI, full-scope, and restricted-scope eligibility tiers.",
    "mc-355": "Governs Medi-Cal categorical linkage criteria, establishing required links to cash aid programs, federal poverty level groups, or disability.",
    "mc-356": "Details Aged, Blind, or Disabled (ABD) linkage requirements under Non-MAGI Medi-Cal, disability verification, and age thresholds.",
    "mc-357": "Governs the Department of Disability Services Division (DDSD) referral process for comprehensive medical disability evaluations.",
    "mc-358": "Outlines Medically Indigent Child and Adult linkage criteria, establishing coverage for individuals who lack standard categorical linkage.",
    "mc-359": "Details extended postpartum Medi-Cal coverage, guaranteeing 12 months of continuous full-scope medical benefits following the end of pregnancy.",
    "mc-360": "Governs Transitional Medi-Cal (TMC) and Four-Month Continuing Medi-Cal (FMC), providing extended health coverage when family income exceeds limits due to earnings or child support.",
    "mc-361": "Details specialized Medi-Cal programs for non-citizens, including PRUCOL status, humanitarian parolees, and state-funded full-scope expansion.",
    "mc-362": "Establishes Pickle Amendment eligibility, preserving full Medi-Cal for individuals who lost SSI/SSP due to Social Security Cost-of-Living Adjustments (COLAs).",
    "mc-363": "Governs Medi-Cal coverage for foster care youth, former foster youth up to age 26, and children receiving Adoption Assistance Program (AAP) benefits.",
    "mc-364": "Details special no-cost Medi-Cal programs for pregnant women and children under 19 with family income up to statutory Federal Poverty Level limits."
}

updated = 0
for d in docs:
    did = d["id"]
    if did in MC_REAL_FIXES:
        d["summary"] = MC_REAL_FIXES[did]
        updated += 1

with open(DOCS_PATH, "w") as f:
    json.dump(docs, f, indent=2)

print(f"Updated {updated} Medi-Cal sections with exact title-matched summaries.")
