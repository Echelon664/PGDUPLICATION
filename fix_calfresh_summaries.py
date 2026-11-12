#!/usr/bin/env python3
"""
Replace 44 CalFresh quick policy summaries that did not match their PDFs.

Each summary below was rewritten from the text of the document's own local PDF
(data/pdfs/), after an audit found the previous summaries contained amounts,
forms, deadlines or topics that the PDF does not state. Updates
data/documents.json and the copy embedded in templates/index.html.

Note: enrich_calfresh_summaries.py still holds the old text for these sections;
re-running it would undo these corrections. Run this script after it if you do.

Usage:
    python3 fix_calfresh_summaries.py            # rewrite files
    python3 fix_calfresh_summaries.py --dry-run  # report only
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS_PATH = os.path.join(ROOT, "data", "documents.json")
TEMPLATE_PATH = os.path.join(ROOT, "templates", "index.html")
EMBED_MARKER = "const EMBEDDED_DOCS = "

# Keyed by document id. Section numbers are in the comments.
CORRECTED = {
    # ---- Wrong PDF attached: summary now describes the PDF that is there ----
    # SN 21-08 (title) -> PDF is CalWORKs SN 21-15
    "cf-106": "Note: the PDF attached to this entry is not SN 21-08. It is CalWORKs Special Notice 21-15, Child Care Regional Market Rate Ceilings (revised 12/01/2021). Under Assembly Bill 131, new Regional Market Rate (RMR) ceilings for licensed child care providers took effect January 1, 2022, set at the 75th percentile of the 2018 RMR survey or the ceilings as of December 31, 2021, whichever is greater; license-exempt care is reimbursed at 70% of the Family Child Care Home rate. Child Care Case Managers must send affected families a timely Child Care Change Notice of Action (NA 833).",
    # SN 21-05 (title says FPL increases) -> PDF is the January 2022 SSA COLA notice
    "cf-116": "Note: despite this entry's title, the attached PDF is Special Notice 21-05, January 2022 Social Security Administration (SSA) Cost of Living Adjustment (COLA) and Related Changes, written for Medi-Cal processing. It announces a 5.9 percent COLA to SSA Title II Retirement, Survivors, and Disability Insurance payments effective 1/1/2022 and states that the increase does not apply to Federal Poverty Level (FPL) programs until April 2022. Staff use the updated 2022 Maintenance Need Assistance Standards chart (SSI/SSP payment levels, Pickle disregard, Medicare premiums) and must not apply negative actions during the public health emergency.",

    # ---- Summary described different content than the PDF ----
    # 63-902
    "cf-100": "Explains which work registrants are deferred from the Employment & Training (E&T) program: refugees enrolled with Resettlement Agencies (a substitute program), veterans honorably discharged from the United States Armed Forces, and victims of domestic violence. Deferred veterans and domestic violence victims may volunteer for E&T. Veterans verify discharge with a DD 214 or Statement of Service and are temporarily deferred while it is requested; a domestic violence deferral can be verified by the customer's statement. A refugee who fails without good cause to comply with Resettlement Agency requirements loses the deferral.",
    # 63-455
    "cf-088": "Covers management of CalFresh overissuance (OI) claims. Explains which state or county collects when a household moves (inter-state and inter-county claims). Sets the claims establishment threshold at $400.00 for closed cases with an Administrative Error (AE) or Inadvertent Household Error (IHE) effective June 1, 2019; the threshold does not apply to Intentional Program Violation (IPV) or Quality Control claims. Describes when collection may be suspended (household cannot be located or cost exceeds recovery), the number of demand letters required, other collection actions such as tax refund intercept, lottery offsets and wage garnishments, and delinquent claims.",
    # 63-222
    "cf-035": "Defines earned income that must be counted in the CalFresh budget: any monetary compensation received for the performance of work. Lists countable types including wages, salaries, diverted wages, In Home Supportive Services (IHSS) wages, military pay and special allowances such as Basic Allowance for Housing (BAH), pay advances, recurring severance payments, striker's benefits received for picketing, training allowances, AmeriCorps VISTA stipends received by an applicant, and Workforce Investment Act (WIA) on-the-job training earnings. Refers to Section 63-224 for exclusions and Section 63-225 for self-employment.",
    # 63-602
    "cf-093": "Question-and-answer handbook on non-financial eligibility. Covers residents of drug/alcohol treatment centers that lack FNS certification, drug felon cases (a felony conviction for obtaining a controlled substance, a felony warrant from another state), household composition questions (divorce, foster care children spending time with a parent, a grandmother with guardianship of grandchildren), probation/parole violation information provided by law enforcement, and an adult student exerting parental control.",
    # 63-605
    "cf-095": "Question-and-answer handbook with one topic: dependent care versus tuition fees. Confirms that dependent care costs are deductible when needed for a household member to accept or continue employment, comply with CalFresh Employment and Training requirements, or attend training or education preparatory to employment, but tuition is not a deductible expense. The worker must differentiate tuition from after-school child care, and the recipient must provide documentation of the child care expense.",
    # 63-610
    "cf-098": "Question-and-answer handbook on replacement of food due to a household misfortune. Finds that food lost when a refrigerator stopped working is a household misfortune and can be replaced, while dry goods destroyed by insects would generally not qualify because it is considered a preventable circumstance. The determination is the county's, based on the circumstances of the case, and must be documented in the case record.",

    # ---- Specific facts contradicted by the PDF ----
    # 63-232
    "cf-041": "Details the excess medical deduction for household members who are elderly and/or disabled. Members who verify medical expenses of $35.01 to $185 per month receive the Standard Medical Deduction (SMD) of $150 per month; households with verified expenses over $185 may claim actual expenses in excess of $35. Countable expenses include prescription drugs, dentures, eyeglasses, prosthetics, health insurance and Medicare premiums, service animals, transportation to health care, and attendant or home health aide costs; special diets are excluded. Expenses must be verified, but failure to verify must not deny, delay or discontinue eligibility.",
    # 63-454
    "cf-087": "Details recoupment of overissuance (OI) claims. For active cases the household receives an OI notice, repayment agreement and budget computation, and may repay by lump sum, installments, or benefit reduction: 5% or $10, whichever is greater, for Administrative Error (AE) claims and 10% or $10 for Inadvertent Household Error (IHE) claims. Intentional Program Violation (IPV) claims are recouped at 20% or $20, whichever is greater. The household has 90 days to request a hearing. For closed cases the claim establishment threshold is $400.00 for AE and IHE claims. Effective December 31, 2023, AE and IHE claims are compromised for households with an elderly and/or disabled member.",
    # 63-451
    "cf-084": "Explains how overissuance (OI) claims are established and classified as Inadvertent Household Error (IHE), Administrative Error (AE), or Intentional Program Violation (IPV). Effective July 1, 2022, a non-fraud claim may be established only for months within 24 months of the date of discovery. Threshold amounts: no claim is established for an active AE of $35 or less or for a closed AE or IHE of $400 or less; an active IHE of $1 or more is established. All adult household members are responsible. Under the Lomeli v. Saenz settlement, AE claims are recouped at 5% or $10, whichever is greater, for 36 months, after which the remaining balance is compromised.",
    # 63-359
    "cf-079": "Governs Inter-County Transfers (ICT) when a CalFresh household moves to another California county. The county notified of the move initiates the ICT within seven business days, and the transfer must be completed within 30 days of notification. An ICT does not require the household to complete a new application, recertification, or interview, or to resubmit verifications. The sending county notifies the customer with the NA 1268 and forwards the CF 215 and case documents; the receiving county sends the NA 1267, continues the existing SAR cycle and recertification, and processes Transitional CalFresh cases.",
    # 63-115
    "cf-009": "Requires an interview at initial certification and at least once every 12 months thereafter. The interview must be completed by phone unless the customer is unable to do so or requests otherwise; customers without a phone or with a hardship may be scheduled for a face-to-face or home visit interview. Staff must resolve unclear information, explain rights, responsibilities and reporting requirements, and inform non-English-speaking customers of their right to an interpreter. When an interview is missed, a Notice of Missed Interview (NOMI) is sent; if the customer does not reschedule or fails to attend, the application is denied on the 30th day.",
    # 63-501
    "cf-090": "Governs Disaster CalFresh (DCF), available when a Presidential Major Disaster Declaration with Individual Assistance has been declared and FNS approves the county's request. Provides one month of food benefits at the maximum allotment for the household size to affected households that were not receiving CalFresh; current recipients may receive disaster supplements. Households apply in person, online or by phone using the Application for Disaster CalFresh (CF 385) during an application period that is usually seven days, and must be interviewed. Benefits must be available within 72 hours of application. Eligibility is evaluated over a 30-day benefit period using a net income and resource test.",
    # 63-274
    "cf-052": "Covers SAR 7 processing: notices, late and incomplete reports, good cause and restoration. Households are asked to submit the SAR 7 by the 5th day of the submit month; it is late if received after the 11th day. The X NOA (NA 960X SAR) notifies the household that a SAR 7 has not been received, the Y NOA (NA 960Y SAR) that it was received but incomplete, and the SAR 90 lists items still missing. Discontinued cases may provide a completed report on the extended filing date, the first working day after the submit month. Benefit decreases require timely 10-day notice; increases do not. Good cause must be evaluated before restoration.",
    # 63-509
    "cf-091": "Allows replacement of food purchased with CalFresh that is destroyed in a household misfortune such as a power outage, fire, or disaster. The household has ten days from the date of the loss to request replacement and submit the signed Replacement or Disaster Supplement Affidavit (CF 303); otherwise no replacement benefits are issued. The misfortune is verified, or the customer's statement on the CF 303 is accepted when verification is unavailable. Replacement benefits must be issued within two days of receiving the CF 303 and equal the food lost, up to one month's allotment.",
    # 63-168
    "cf-031": "Covers replacement of CalFresh benefits stolen electronically by skimming or scamming while the EBT card is in the household's possession. The card is deactivated and replaced, and the household must submit a Report of Electronic Theft of Benefits (EBT 2259) within 90 days of the theft; later requests are denied. Replacement benefits are issued no later than 10 days after the completed form is received. A household may receive two countable replacements per Federal Fiscal Year, each limited to the amount stolen or two times the benefits issued before the first theft, whichever is less. Suspected fraud is referred to the Bureau of Public Assistance Investigations (BPAI), which may delay replacement up to 25 calendar days.",
    # 63-302
    "cf-056": "Defines CalFresh household classifications, which determine factors such as verification requirements and certification periods. Public Assistance CalFresh (PACF): all members receive federal CalWORKs benefits, SSI, or Tribal TANF. Non-Assistance CalFresh (NACF): at least one member does not receive federal CalWORKs or SSI, or receives State CalWORKs. A mixed household is considered NACF. Non-household members such as a foster care child or an ineligible noncitizen do not affect classification. Other classifications are Categorical Eligibility (CE) and Modified Categorical Eligibility (MCE), covered in Section 63-120.",
    # 63-355
    "cf-075": "Sets procedures for third-party requests for case information. Questionable requests are forwarded with a written statement to the Family Resource Center (FRC) Manager for approval; inquiries on closed cases go to the Public Assistance Information Unit (PAI). Board of Supervisors inquiries are generally answered without releasing information about a specific applicant/recipient unless consent is given. Release to absent parents, family or friends requires the applicant/recipient's written consent. Defense attorney requests without a release go to the HHSA Subpoena Liaison. Law enforcement requests must be in writing from the head of the agency and specify that an arrest warrant has been issued.",

    # ---- Details that did not appear in the PDF ----
    # 63-201
    "cf-033": "Details the CalFresh resource evaluation for households that are not Categorically Eligible (CE) or Modified Categorically Eligible (MCE), whose non-exempt resources must not exceed the limit listed in Section 63-1101. Countable resources include liquid resources (cash on hand, checking and savings accounts, stocks, bonds, IRAs and accessible Keogh plans) and non-liquid resources valued at equity. Explains the treatment of jointly owned resources, resources of excluded household members, sponsor resources deemed to sponsored noncitizens (reduced by $1,500), and residents of battered person shelters. Resources are evaluated at application, SAR 7 and recertification.",
    # 63-247
    "cf-045": "Substantial lottery or gambling winnings (a cash prize won in a single game, ticket or bet) equal to or greater than the elderly or disabled (E/D) resource limit make the household ineligible, and must be reported within 10 calendar days of receipt as a mandatory mid-period report. The amount is determined before taxes, and each winning is evaluated individually, not combined. The entire household is discontinued with timely notice. Households may reapply at any time but are not Categorically Eligible or MCE the first time they are certified afterward, so the gross income, net income and resource tests apply.",
    # 63-283
    "cf-053": "Covers mid-period reports, categorized as mandatory, voluntary, or county-initiated. Households must report within 10 days when gross income exceeds the Income Reporting Threshold (IRT), when an ABAWD's work or training hours drop below 20 hours per week or 80 hours a month, or when they receive substantial lottery or gambling winnings at or above the Elderly or Disabled (E/D) resource limit. Reports that would decrease benefits are generally not acted on mid-period, with listed exceptions; a No-Change NOA is sent and the change is addressed at the next SAR 7 or recertification. County-initiated changes are acted on regardless of impact. Households are informed through the SAR 2 notice.",
    # 63-234
    "cf-043": "Covers shelter deductions for unhoused households that do not receive free shelter for the entire month. They may receive the homeless shelter deduction (amount listed in Section 63-1101) or claim actual shelter expenses such as hotel and motel costs, homeless shelter fees, and vehicle expenses when living in a vehicle, whichever is more beneficial. The homeless shelter deduction and a utility allowance cannot be received at the same time. Allowable vehicle expenses include payments, collision and comprehensive insurance, parking and maintenance, but not fuel. Reported shelter expenses are accepted without verification unless questionable.",
    # 63-117
    "cf-010": "Details mandatory and optional verifications. The household has primary responsibility for providing verification, but staff must first attempt electronic verification through the Income Eligibility Verification System (IEVS), Payment Verification System (PVS), MEDS and the Work Number, assist customers as needed, and accept any reasonable verification. Mandatory verifications are gross non-exempt income, non-citizen eligibility, identity, Social Security Numbers and residency. Items such as medical expenses, disability, student exemption and child support payments affect only the benefit amount: if unverified the deduction is not allowed, but the case is not denied. Explains when information is questionable.",
    # 63-161
    "cf-026": "Requires each household member applying for CalFresh to provide a Social Security Number (SSN) or apply for one before certification; failure or refusal without good cause makes that individual ineligible. A Social Security card is not required, since a verbal or written statement is sufficient, and SSNs are validated through IEVS. For an unresolved data mismatch, a Request for Verification (CW 2200) allows 10 days. Expedited Services households need not provide an SSN until after their first allotment. Newborns remain eligible until the next recertification or the sixth month after birth, whichever is later. Staff assist with a Social Security Administration Referral Notice (MC 194).",
    # 63-162
    "cf-027": "Defines CalFresh eligibility for students enrolled in an institution of higher education, who must meet one exemption. Exemptions include being age 17 or younger or age 50 or older, physically or mentally unfit for employment, enrolled less than half time, receiving disability-based income, receiving a TANF-funded Cal Grant A or B, receiving CalWORKs, working at least 20 hours per week or 80 hours per month, exerting parental care and control of a child under age 6, or participating in a Local Program that Increases Employability (LPIE). Student status is evaluated at intake and recertification; adult education programs are not considered higher education.",
    # 63-167
    "cf-029": "A fraud referral is made to the Bureau of Public Assistance Investigation (BPAI) when there are allegations or suspicions of fraud, or questionable information that cannot be resolved. Applicants are referred before benefits are granted; recipients within 5 working days of determining a referral is needed. Lists fraud indicators such as questionable residency, suspected duplicate aid and unreported income. A referral must not cause a denial or discontinuance unless findings change eligibility, and must not delay CalFresh or Expedited Service benefits. Staff must first try to resolve discrepancies using IEVS, MEDS and The Work Number.",
    # 63-301
    "cf-055": "Explains certification periods, the number of months a household is certified to receive benefits without a new application. All households are assigned a 12-month period unless all adult members are elderly or disabled (24 months), all members are elderly or disabled with no earned income (36 months), or members live on an Indian Reservation (24 months). A period is generally no fewer than 4 months, though one or two months may be assigned if ineligibility appears likely. Certification periods are matched with Semi-Annual Reporting (SAR) cycles and may be shortened only with a timely Notice of Action, or lengthened up to the maximum for the household type.",
    # 63-330
    "cf-062": "Explains the reversal of California's SSI/SSP cash-out policy, in place since 1974. Effective June 1, 2019, individuals receiving SSI/SSP are eligible for CalFresh if they meet all other eligibility criteria. Households in which all members are SSI/SSP recipients are potentially eligible from that date; ongoing households with an excluded SSI/SSP member have the change applied at the next periodic report, recertification, or when requested. Previously excluded members' income, resources and deductions are then counted. SSI/SSP income is verified through PVS, IEVS and MEDS before requesting documentation.",
    # 63-113
    "cf-008": "Customers may designate an adult non-household member as an Authorized Representative (AR) to complete the application and recertification, obtain and use the EBT card, and complete required reporting and forms. Designation is made on the application, a CalFresh AR designation form, or a signed written statement. An AR must be an individual, not an organization; residents of Drug/Alcohol Treatment Centers must use an AR employed by the center. The household is responsible for any overissuance caused by incorrect information from the AR. Eligibility employees, authorized retailers, homeless meal provider employees and persons disqualified for an IPV generally cannot be ARs.",
    # 63-118
    "cf-011": "Describes the Income and Eligibility Verification System (IEVS), which matches against state and federal databases and includes Applicant and Recipient IEVS, the Payment Verification System (PVS), New Hire Registry, Fleeing Felon Match and California Lottery Match. Most matches are processed at application and recertification; PVS matches are Verified Upon Receipt. Follow-up must generally be completed within 45 days of receipt, and granting benefits must not be delayed waiting for IEVS data. Information must be independently verified, with the customer given the first opportunity, before case action is taken (except PVS and lottery winnings).",
    # 63-124
    "cf-016": "Residents of Domestic Violence (DV) shelters are considered separate households and may apply for CalFresh on their own behalf or through an Authorized Representative. A resident who already received benefits for the month as a member of the abuser's household may apply as a separate household and may be eligible for an additional allotment, issued under a new case and EBT card. Only the income, resources and expenses the resident is responsible for are counted; resources held jointly with the former household are not considered available. Describes the actions and notices required on the former case.",
    # 63-152
    "cf-020": "Identity and residency must be verified. When an Authorized Representative applies, the identity of both the representative and the head of household is verified; customers without identification may use a collateral contact. Any document that reasonably establishes identity or residency must be accepted. Customers must live in the county where they apply, but a permanent dwelling, fixed mailing address or intent to reside permanently is not required. Homeless households meet residency by stating they live in the county. Out-of-county EBT use is not a reason to discontinue benefits, and discontinuance for whereabouts unknown is not permitted.",
    # 63-153
    "cf-021": "Limits CalFresh participation to U.S. Citizens and qualified Non Citizens, updated for H.R. 1 (signed July 4, 2025). Qualified Non Citizens are Non Citizen U.S. Nationals, Lawful Permanent Residents (LPRs), individuals residing under a Compact of Free Association (COFA) agreement, and Cuban and Haitian Entrants. U.S. Citizens include those born in the 50 states, the District of Columbia, Puerto Rico, Guam, the U.S. Virgin Islands or the Northern Mariana Islands, and naturalized, acquired or derived citizens. A statement is sufficient verification unless questionable. Certain LPRs face a five-year waiting period; those ineligible may qualify for CFAP.",
    # 63-203
    "cf-034": "Lists resources excluded for households that are not Categorically Eligible or MCE. Exclusions include the home and surrounding property, income-producing property, household goods and personal effects, one burial plot per member, the cash value of life insurance, all vehicles, resources with an equity value of $1,500 or less, property essential to employment or self-employment, TANF Individual Development Accounts, disaster loans and grants, and inaccessible resources such as security deposits, property in probate and irrevocable trust funds. Excluded retirement savings and pension plans are listed in a separate desk aid.",
    # 63-351
    "cf-069": "Outlines the worker's general responsibilities: determining eligibility for the assigned case action, explaining program requirements in simple, understandable terms, advising households of their rights and responsibilities during the application and recertification interview, ensuring lost, stolen or underpaid EBT benefits are replaced in the current month, and processing claim determinations under Section 63-450. Notes that benefit availability is staggered over the first ten days of the month and that non-discrimination information is now found in the Eligibility Desk Guide.",
    # 63-354
    "cf-073": "Confidential information may be released without the customer's consent only for purposes directly connected with the administration of public social services programs, and all requests are recorded in case comments. Provides an Authorized Disclosure List of agencies that most often make authorized inquiries, such as County Counsel, the District Attorney, EDD, the Social Security Administration and Housing Authorities. Research organizations and graduate students must first submit project information. Otherwise release requires customer consent: written authorization must be signed and dated and expires after one year; telephone authorization covers one-time contacts.",
    # 63-356
    "cf-076": "Information provided solely by, or authorized by, the applicant/recipient (such as bank, employment and medical verification requests) may be released to them or their authorized representative, and staff may photocopy specific items. Photocopies of the whole case file or of case narratives are not provided. Information given confidentially by a third party, such as PAFD reports and informant identity, is not disclosed. IEVS reports may be released only when they verify previously reported information; mismatched or previously unreported information is withheld until the discrepancy is clarified.",
    # 63-357
    "cf-077": "Sets Family Resource Center (FRC) procedures for inspection of case records by applicants/recipients or their authorized representatives. The complete record is made available after privileged communications and information not provided or authorized by the client are removed. Inspection is permitted only during normal work hours, in a private room with the worker present; reviewers may make notes but may not remove, alter, photocopy or photograph records, though staff may copy specific items. Privileged material includes physician reports, PAFD reports, informer identity, Child Abuse Hotline reports, and lawyer-client and spousal communications.",
    # 63-358
    "cf-078": "Explains how staff respond to subpoenas and subpoenas duces tecum. Staff fully cooperate with District Attorney subpoenas on matters directly related to the administration of public social services and appear as directed. Subpoenas from private attorneys, Legal Aid or the Public Defender on unrelated matters such as divorce or child custody go to the Subpoena Liaison, who asks the attorney to withdraw them under W&I Code 10850. Staff must not accept subpoenas addressed to the Custodian of Record. If the attorney refuses to withdraw, the employee appears with County Counsel's Points and Authorities and does not testify until it has been presented to the judge.",
    # 63-370
    "cf-081": "Describes the state-funded Minimum Nutrition Benefit (MNB) pilot, operating December 1, 2025 through November 30, 2026. It provides up to 12 months of supplements that bring total benefits up to $60 for households eligible for less than $60 monthly in CalFresh that had Elderly Simplified Application Project (ESAP) status on or before December 1, 2025 and have at least two eligible members. When benefits are reduced by recoupment, MNB is calculated on the full CalFresh amount. Households receiving SNB or a prorated benefit are ineligible. No overissuances are established for MNB, and it is not replaced for disaster, household misfortune or electronic theft.",
    # 63-604
    "cf-094": "Question-and-answer handbook on income. Covers tribal casino disbursements (the first $2,000 per calendar year is excluded for tribal members when paid from interests in trust or restricted land), disaster relief employment income and disaster unemployment assistance (both excluded), Paid Family Leave, Ross Grant payments, self-employment room rental expenses, transitional youth programs such as THP-Plus, vendor payments and the shelter deduction, and work study grants.",
    # 63-609
    "cf-097": "Question-and-answer handbook on claims. Explains that the reasonably anticipated CalWORKs grant, not a recalculated grant, is used to compute an overissuance or underissuance; that all adult household members, including adult children, are liable for overissuances; that a claim can be collected from two separate households at the same time; that excluded adult members can be required to repay, though not from SSI/SSP benefits; and how to calculate an overissuance when unreported self-employment income is averaged over the year.",
    # SN 21-03
    "cf-113": "Special Notice (effective February 12, 2021) on customers reporting that Unemployment Insurance Benefits (UIB) claims were filed using their personal information without their knowledge. Lists examples of EDD benefit fraud and introduces a County Information Notice with resources for victims. In identity theft cases staff will not require a police report or EDD documents; a signed affidavit is acceptable verification to resolve reporting discrepancies. Customers are directed to the EDD Fraud Hotline, the SSA online report and the California Attorney General's identity theft resources; suspected public assistance fraud is referred to BPAI.",
}


def update_template(summaries: dict) -> int:
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html = f.read()
    start = html.index(EMBED_MARKER) + len(EMBED_MARKER)
    embedded, length = json.JSONDecoder().raw_decode(html[start:])
    changed = 0
    for item in embedded:
        new = summaries.get(item.get("id"))
        if new and item.get("summary") != new:
            item["summary"] = new
            changed += 1
    # "</" must stay escaped so the JSON cannot close the <script> tag.
    new_json = json.dumps(embedded).replace("</", "<\\/")
    with open(TEMPLATE_PATH, "w", encoding="utf-8") as f:
        f.write(html[:start] + new_json + html[start + length:])
    return changed


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        docs = json.load(f)

    by_id = {d["id"]: d for d in docs}
    missing = [i for i in CORRECTED if i not in by_id]
    if missing:
        print(f"Unknown document ids: {missing}")
        return 1

    changed = 0
    for doc_id, summary in CORRECTED.items():
        if by_id[doc_id].get("summary") != summary:
            by_id[doc_id]["summary"] = summary
            changed += 1
    print(f"{changed} of {len(CORRECTED)} summaries differ from documents.json.")

    if dry_run:
        print("Dry run: nothing written.")
        return 0

    with open(DOCS_PATH, "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2)
    n = update_template(CORRECTED)
    print(f"Wrote {DOCS_PATH}")
    print(f"Updated {n} embedded summaries in {TEMPLATE_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
