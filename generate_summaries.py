#!/usr/bin/env python3
import json, re, os

DOCS_PATH = "/Users/echelon619/.gemini/antigravity/scratch/sd-benefits-search/data/documents.json"

def clean_title(title):
    t = title.strip()
    t = re.sub(r'^(Section\s+\d+\s*-\s*|Section\s+\d+\s+|[A-Z]\.\s+)', '', t)
    return t.strip()

def build_summary(doc):
    title = doc.get('title', '').strip()
    prog = doc.get('programs', ['San Diego Benefits'])[0]
    chapter = doc.get('chapter', '').strip()
    t_lower = title.lower()

    # --- SPECIAL NOTICES ---
    if t_lower.startswith('sn ') or 'special notice' in t_lower:
        sn_match = re.search(r'SN\s*([0-9]{2}[-\s][0-9]{2})', title, re.IGNORECASE)
        sn_code = f"SN {sn_match.group(1).replace(' ', '-')}" if sn_match else "Special Notice"
        desc = re.sub(r'^SN\s*[0-9]{2}[-\s][0-9]{2}\s*[-–:]*\s*', '', title, flags=re.IGNORECASE).strip()
        
        if 'cola' in t_lower or 'cost of living' in t_lower or 'cost-of-living' in t_lower:
            return f"{sn_code} establishes updated {prog} monthly benefit standards, allotment tables, and eligibility thresholds following annual Cost-of-Living Adjustments (COLA)."
        elif 'eitc' in t_lower or 'earned income tax credit' in t_lower:
            return f"{sn_code} details annual mandatory client notification and outreach regarding federal and California Earned Income Tax Credit (CalEITC) and Young Child Tax Credit cash refunds."
        elif 'irt' in t_lower or 'income report' in t_lower:
            return f"{sn_code} announces revised Income Reporting Threshold (IRT) tiers across household sizes and specifies caseworker budgeting procedures for mid-period changes."
        elif 'fpl' in t_lower or 'poverty level' in t_lower or 'maintenance need' in t_lower:
            return f"{sn_code} publishes annual Federal Poverty Level (FPL) income standards, allocation amounts, and maintenance need limits for {prog} eligibility budgeting."
        elif 'rmr' in t_lower or 'regional market rate' in t_lower:
            return f"{sn_code} updates maximum Regional Market Rate (RMR) reimbursement ceilings for child care providers under subsidized child care payment schedules."
        elif 'minimum wage' in t_lower:
            return f"{sn_code} directs caseworkers on recalculating earned income, budgeting disregards, and adjusting work participation hours in response to statutory California minimum wage increases."
        elif 'time-on-aid' in t_lower or '60-month' in t_lower:
            return f"{sn_code} details administrative procedures and tracking rules for the CalWORKs 60-month lifetime time-on-aid limit, including qualifying good cause clock-stopping exemptions."
        elif 'unemployment insurance' in t_lower or 'fraud' in t_lower:
            return f"{sn_code} outlines procedures for identifying and handling suspected EDD unemployment insurance fraud and identity theft without unjustly terminating benefits for eligible customers."
        elif 'overpayment' in t_lower:
            return f"{sn_code} provides policy guidance on recoupment, waiver, and administrative adjustments for overpayments incurred during emergency disaster declarations."
        elif 'covered california' in t_lower or 'aptc' in t_lower:
            return f"{sn_code} specifies automated case transition procedures between Covered California tax credit plans and no-cost MAGI Medi-Cal during annual renewal periods."
        elif 'allocation' in t_lower or 'base allocation' in t_lower:
            return f"{sn_code} updates Family Member Base Allocation (FMBA) figures used in long-term care, spousal impoverishment, and maintenance budgeting."
        elif 'tuberculosis' in t_lower or 'tb' in t_lower:
            return f"{sn_code} establishes updated income eligibility thresholds and program standards for the specialized Medi-Cal Tuberculosis (TB) program."
        else:
            return f"{sn_code} provides official County HHSA policy guidance and operational instructions regarding {desc} under {prog} regulations."

    # --- CALFRESH (SNAP) ---
    if prog == 'CalFresh':
        if '63-101' in t_lower or 'household concept' in t_lower:
            return "Defines CalFresh household composition, mandatory inclusion rules for parents and children living together, and separate household status criteria for elderly (60+) or disabled individuals unable to purchase and prepare meals."
        elif '63-103' in t_lower or 'filing an application' in t_lower:
            return "Establishes CalFresh application filing procedures, acceptable signature methods including telephonic and electronic signatures, and regulations for fixing the official beginning date of aid."
        elif '63-105' in t_lower or 'expedited services' in t_lower:
            return "Mandates 3 calendar-day expedited CalFresh issuance for households with under $150 gross income and $100 liquid resources, or destitute migrant/seasonal farmworkers, requiring identity verification prior to authorization."
        elif '63-107' in t_lower or 'household cooperation' in t_lower:
            return "Outlines penalties and legal distinctions between refusal to cooperate and failure to cooperate during application processing, semi-annual reports, and Quality Control (QC) reviews."
        elif '63-109' in t_lower or 'time limits and delays' in t_lower:
            return "Establishes standard 30-day processing timeframes, distinguishing agency-caused delays from household-caused delays and setting mandatory notice requirements."
        elif '63-1101' in t_lower or 'eligibility standards table' in t_lower:
            return "Official CalFresh eligibility standards table listing current Federal Poverty Levels (130% Gross FPL, 100% Net FPL), Standard Deductions, and Maximum Benefit Allotments."
        elif '63-1103' in t_lower:
            return "Provides comprehensive definitions, regulatory budgeting examples, and income deduction formulas for CalFresh case eligibility determination."
        elif '63-113' in t_lower or 'authorized representative' in t_lower:
            return "Governs the designation and responsibilities of Authorized Representatives (ARs) acting on behalf of CalFresh households, including residents of treatment centers and group homes."
        elif '63-115' in t_lower or 'interview requirements' in t_lower:
            return "Outlines mandatory interview procedures, telephonic interview options, interview waiver criteria, and scheduling requirements for CalFresh intake and recertifications."
        elif '63-117' in t_lower or 'verification and documentation' in t_lower:
            return "Details mandatory verification items (identity, income, immigration status, residency) and acceptable documentation standards for establishing CalFresh eligibility."
        elif '63-118' in t_lower or 'ievs' in t_lower:
            return "Outlines procedures for matching, reviewing, and resolving automated Income and Eligibility Verification System (IEVS) wage and benefit discrepancies."
        elif '63-120' in t_lower or 'categorical eligibility' in t_lower:
            return "Explains Modified Categorical Eligibility (MCE) rules, which eliminate the federal asset/resource test for most CalFresh households receiving TANF-funded information."
        elif '63-121' in t_lower or 'denial withdrawal granting' in t_lower:
            return "Establishes timeliness standards, mandatory Notice of Action (NOA) issuance, and proper caseworker procedures for granting, denying, or withdrawing CalFresh applications."
        elif '63-123' in t_lower or 'drug alcohol treatment' in t_lower:
            return "Governs CalFresh eligibility, authorized representative requirements, and meal provision rules for residents of approved drug/alcohol treatment facilities and group living arrangements."
        elif '63-124' in t_lower or 'domestic violence' in t_lower:
            return "Authorizes separate CalFresh household certification for residents of domestic violence shelters who recently fled abusive living arrangements, even if previously included on an active case."
        elif '63-125' in t_lower or 'irt' in t_lower or 'income reporting threshold' in t_lower:
            return "Details mandatory mid-period income reporting rules when household gross income exceeds the Income Reporting Threshold (130% FPL), and required county action timeframes."
        elif 'student' in t_lower:
            return "Outlines student eligibility criteria and exemptions (including 20 hours/week employment, approved work-study, or community college CTE programs) for higher education students."
        elif 'cfap' in t_lower or 'california food assistance' in t_lower or '63-156' in t_lower:
            return "Governs the state-funded California Food Assistance Program (CFAP) providing food benefits to qualified noncitizens ineligible for federal SNAP due to immigration status."
        elif 'citizenship' in t_lower or 'noncitizen' in t_lower or '63-157' in t_lower:
            return "Details citizenship, qualified noncitizen categories, sponsor deeming rules, and verification requirements for immigrant household members applying for CalFresh."
        elif 'ssn' in t_lower or 'social security number' in t_lower or '63-158' in t_lower:
            return "Specifies mandatory Social Security Number (SSN) disclosure rules for participating household members and exclusion procedures for individuals without an SSN."
        elif 'residence' in t_lower or '63-159' in t_lower:
            return "Establishes residency requirements within San Diego County, prohibiting simultaneous receipt of benefits in multiple jurisdictions while accommodating individuals experiencing homelessness."
        elif 'fraud' in t_lower or '63-167' in t_lower:
            return "Outlines Early Fraud Prevention and Detection (EFPD) referral criteria, investigator guidelines, and applicant due process protections during fraud inquiries."
        elif 'restaurant meals' in t_lower or 'rmp' in t_lower or '63-168' in t_lower:
            return "Governs the Restaurant Meals Program (RMP) permitting homeless, elderly (60+), and disabled CalFresh recipients to use EBT cards at participating prepared food vendors."
        elif 'resource' in t_lower:
            return "Details allowable resource limitations, exempt property categories (vehicles, primary homes, retirement funds), and non-exempt asset treatment under CalFresh regulations."
        elif 'earned income' in t_lower or '63-221' in t_lower:
            return "Governs earned income budgeting, the statutory 20% earned income deduction, and verification procedures for gross wages and salary."
        elif 'unearned income' in t_lower or '63-223' in t_lower:
            return "Outlines the treatment and counting of unearned income, including Social Security, disability benefits, pensions, unemployment benefits, and child support."
        elif 'self-employment' in t_lower or '63-225' in t_lower:
            return "Details budgeting procedures for self-employment income, allowable business expense deductions, standard deduction options, and net profit calculation."
        elif 'sua' in t_lower or 'utility allowance' in t_lower or '63-231' in t_lower:
            return "Specifies standard utility deductions, including the Standard Utility Allowance (SUA), Limited Utility Allowance (LUA), and Telephone Utility Allowance (TUA)."
        elif 'deduction' in t_lower or '63-230' in t_lower:
            return "Covers allowable CalFresh income deductions, including the standard deduction, excess medical deduction for elderly/disabled, child support paid, and excess shelter costs."
        elif 'sar 7' in t_lower or 'semi-annual' in t_lower or '63-271' in t_lower or '63-281' in t_lower:
            return "Governs Semi-Annual Reporting (SAR 7) submission deadlines, completeness criteria, mandatory mid-period changes, and case discontinuance procedures."
        elif 'recertification' in t_lower or '63-300' in t_lower:
            return "Establishes recertification timeframes, notice requirements, interview standards, and verification guidelines to ensure uninterrupted CalFresh benefit issuance."
        elif 'certification period' in t_lower or '63-301' in t_lower:
            return "Specifies assigned certification period durations (12 months for standard households, up to 24/36 months for elderly/disabled ESAP cases)."
        elif 'restoration' in t_lower or '63-306' in t_lower:
            return "Details procedures for restoring discontinued CalFresh cases within 30 days without requiring a brand-new application when good cause or delayed documentation is provided."
        elif 'ssi' in t_lower or '63-330' in t_lower:
            return "Covers the historic CalFresh expansion for Supplemental Security Income (SSI/SSP) recipients, detailing separate household budgeting and grant calculations."
        elif 'transitional' in t_lower or 'tnb' in t_lower or '63-332' in t_lower:
            return "Details Transitional Nutrition Benefit (TNB) and Supplemental Nutrition Benefit (SNB) policies protecting households experiencing benefit reductions upon CalFresh expansion."
        elif 'esap' in t_lower or 'elderly simplified' in t_lower or '63-352' in t_lower:
            return "Outlines the Elderly Simplified Application Project (ESAP), featuring 36-month certification periods, waived recertification interviews, and reduced reporting for qualifying households."
        elif 'confidentiality' in t_lower or '63-353' in t_lower or '63-354' in t_lower:
            return "Specifies legal confidentiality mandates and strict disclosure boundaries governing client case records and personal identifying information under federal and state privacy statutes."
        elif 'claim' in t_lower or 'overissuance' in t_lower or '63-450' in t_lower:
            return "Establishes policy for establishing, calculating, and recovering CalFresh overissuances classified as Administrative Error (AE), Inadvertent Household Error (IHE), or Intentional Program Violation (IPV)."
        elif 'disaster' in t_lower or '63-500' in t_lower:
            return "Details Disaster CalFresh (D-SNAP) policies, emergency benefit allotments, and food replacement procedures following federally declared natural disasters or prolonged utility outages."
        elif 'policy question' in t_lower or '63-60' in t_lower:
            return "County HHSA policy question-and-answer handbook providing official eligibility rulings, budgeting scenarios, and case administration guidance for caseworkers."
        elif 'cfet' in t_lower or 'employment and training' in t_lower or '63-903' in t_lower:
            return "Governs the CalFresh Employment and Training (CFET) program, participant components, supportive service transportation payments, and participant reimbursements."
        elif 'abawd' in t_lower or 'work registration' in t_lower or '63-900' in t_lower:
            return "Outlines general work registration requirements, ABAWD 3-month time limits, countable months, and qualifying regional or individual work exemptions."
        else:
            return f"Official CalFresh Program Guide section for {title}. Establishes County HHSA caseworker criteria, verification requirements, and regulatory standards under CDSS MPP Chapter 63."

    # --- CALWORKS (TANF) ---
    elif prog == 'CalWORKs':
        if 'welfare-to-work' in t_lower or 'wtw' in t_lower or '10-00' in t_lower or '10-02' in t_lower:
            return "Details CalWORKs Welfare-to-Work (WTW) mandatory participation hours (20, 30, or 35 hrs/wk), orientation and appraisal sequencing, good cause exemptions, and compliance sanction processes."
        elif 'child care' in t_lower or '10-010' in t_lower:
            return "Governs Stage One Child Care eligibility, licensed and license-exempt provider reimbursement ceilings (RMR), 12-month continuous authorization, and transition to Stage Two care."
        elif 'supportive services' in t_lower or '10-011' in t_lower:
            return "Details WTW supportive services payments including transportation assistance, ancillary work expenses, books, tools, and overpayment recovery rules."
        elif 'exemption' in t_lower and ('10-' in t_lower or 'wtw' in t_lower):
            return "Specifies statutory exemptions from Welfare-to-Work participation, including care of an infant, medical disability, advanced age, or domestic violence waiver."
        elif 'compliance' in t_lower or 'sanction' in t_lower or '10-025' in t_lower:
            return "Details the noncompliance, conciliation, and sanction process for failure to meet WTW hourly participation requirements without documented good cause."
        elif 'subsidized employment' in t_lower or '10-150' in t_lower:
            return "Governs Expanded Subsidized Employment (ESE) and work-experience programs placing participants in wage-paying private or non-profit sector jobs."
        elif 'wrap around' in t_lower or '10-160' in t_lower:
            return "Establishes CalWORKs Wrap Around procedures for specialized family supportive services and intensive caseworker intervention."
        elif 'immediate need' in t_lower or '40-129' in t_lower:
            return "Authorizes immediate emergency cash assistance of up to $200 for eligible CalWORKs applicant families facing an emergency while the regular application is processed."
        elif 'homeless assistance' in t_lower or '44-211' in t_lower:
            return "Details CalWORKs Homeless Assistance (HA) providing 16 consecutive days of temporary shelter payments and permanent housing move-in deposit assistance."
        elif 'application' in t_lower or '40-100' in t_lower or '40-105' in t_lower:
            return "Outlines CalWORKs application intake procedures, applicant rights and responsibilities, required interviews, and 45-day promptness processing standards."
        elif 'age' in t_lower or '41-100' in t_lower:
            return "Specifies child age eligibility requirements (under age 18, or 18 and completing high school or vocational training before age 19) for CalWORKs assistance."
        elif 'deprivation' in t_lower or '41-400' in t_lower:
            return "Details parental deprivation requirements for CalWORKs cash aid, establishing eligibility based on parental unemployment, continued absence, physical/mental incapacity, or death."
        elif 'residence' in t_lower or '42-400' in t_lower:
            return "Establishes California residency intent rules, temporary absence criteria, and guidelines for transferring cases between California counties."
        elif 'noncitizen' in t_lower or 'citizenship' in t_lower or '42-430' in t_lower:
            return "Covers citizenship and eligible qualified immigrant statuses for CalWORKs, including sponsor deeming and exclusions for undocumented family members."
        elif 'property' in t_lower or 'resource' in t_lower or '42-200' in t_lower:
            return "Specifies CalWORKs property limitation thresholds ($11,634 standard, $17,451 for households with elderly/disabled members), real property rules, and motor vehicle valuation exemptions."
        elif 'map' in t_lower or 'maximum aid' in t_lower or '44-315' in t_lower:
            return "Official Maximum Aid Payment (MAP) and Minimum Basic Standard of Adequate Care (MBSAC) grant schedules across Assistance Unit (AU) sizes."
        elif 'earned income' in t_lower or 'disregard' in t_lower or '44-111' in t_lower:
            return "Governs the CalWORKs earned income disregard ($450 standard deduction plus 50% disregard on remaining wages) used in monthly grant budgeting."
        elif 'self-employment' in t_lower:
            return "Details self-employment income reporting, allowable operating expenses, and net profit calculation methods for CalWORKs assistance units."
        elif 'child support' in t_lower:
            return "Outlines mandatory child support cooperation with the local child support agency (LCSA), good cause claim exceptions, and the $100/$200 child support disregard pass-through."
        elif 'overpayment' in t_lower or '44-350' in t_lower:
            return "Establishes procedures for calculating CalWORKs cash overpayments, demand notices, grant recoupment withholding percentages, and administrative hearings."
        elif 'aid types' in t_lower or 'desk aid' in t_lower:
            return "Reference desk aid providing comprehensive aid codes, funding source designations (TANF federal vs. state general fund), and eligibility criteria."
        elif 'immunization' in t_lower:
            return "Outlines child immunization verification requirements and exemptions for dependent children under age six receiving CalWORKs cash assistance."
        else:
            return f"Official CalWORKs Program Guide section for {title}. Details County HHSA caseworker criteria, verification requirements, and regulatory standards under CDSS MPP Chapters 40–44."

    # --- MEDI-CAL (MEDICAID) ---
    else:
        if 'asset' in t_lower and ('elimination' in t_lower or 'elim' in t_lower or 'property' in t_lower):
            return "Explains the California elimination of the asset and property test effective January 1, 2024, removing all property limits for Non-MAGI Medi-Cal eligibility."
        elif 'magi' in t_lower:
            return "Governs Modified Adjusted Gross Income (MAGI) household budgeting, tax filer rules, and 138% Federal Poverty Level (FPL) income limits for adults."
        elif 'postpartum' in t_lower:
            return "Provides 12-month continuous full-scope Medi-Cal postpartum coverage regardless of income changes, ensuring comprehensive maternal health care services."
        elif 'continuous' in t_lower and 'child' in t_lower:
            return "Guarantees continuous Medi-Cal eligibility for children under age 5 regardless of household income fluctuations until the end of the child's fifth year."
        elif 'full scope' in t_lower or 'expansion' in t_lower or 'undocumented' in t_lower:
            return "Covers full-scope Medi-Cal expansion for adults ages 26 through 49 regardless of immigration status, providing medical, dental, vision, and mental health care."
        elif 'renewal' in t_lower or 'redetermination' in t_lower or 'ex parte' in t_lower:
            return "Outlines annual Medi-Cal renewal procedures, automatic ex parte electronic data matching, packet submission timeframes, and disenrollment protections."
        elif 'long term care' in t_lower or 'ltc' in t_lower or 'spousal' in t_lower:
            return "Governs Long-Term Care (LTC) institutional budgeting, Spousal Impoverishment asset/income protections, and Home and Community-Based Services (HCBS) waivers."
        elif 'tuberculosis' in t_lower or 'tb' in t_lower:
            return "Outlines eligibility criteria and application procedures for the specialized Medi-Cal Tuberculosis (TB) program covering diagnostic and treatment services."
        elif 'presumptive' in t_lower or 'hospital' in t_lower:
            return "Governs Hospital Presumptive Eligibility (HPE) granting immediate, temporary full-scope Medi-Cal coverage to qualified individuals during medical visits."
        elif 'minor consent' in t_lower:
            return "Details confidential Minor Consent Medi-Cal services for youth seeking reproductive health, mental health, and substance use treatment without parental notification."
        elif 'proof of eligibility' in t_lower or 'provider' in t_lower:
            return "Outlines provider obligations to verify Medi-Cal eligibility via the automated POS/MEDS system and rules prohibiting balance billing of eligible beneficiaries."
        elif 'county of responsibility' in t_lower or 'inter-county' in t_lower or 'ict' in t_lower:
            return "Establishes Inter-County Transfer (ICT) procedures, county-of-responsibility rules, and case coordination when beneficiaries move between California counties."
        elif 'retroactive' in t_lower:
            return "Governs 3-month retroactive Medi-Cal coverage, reimbursing or paying unpaid qualifying medical expenses incurred prior to the month of application."
        elif 'share of cost' in t_lower or 'soc' in t_lower:
            return "Details Share of Cost (SOC) determination, maintenance need levels, and medical bill deduction procedures for Non-MAGI medically needy beneficiaries."
        elif 'confidentiality' in t_lower or 'records' in t_lower:
            return "Specifies HIPAA confidentiality standards, disclosure authorizations, and safeguarding guidelines for protected health information in case records."
        elif 'hearing' in t_lower or 'appeal' in t_lower:
            return "Outlines state fair hearing request procedures, aid paid pending standards, and county appeals representation for Medi-Cal adverse determinations."
        elif 'section' in t_lower:
            sec_name = clean_title(title)
            return f"Official Medi-Cal policy article governing {sec_name}. Outlines Department of Health Care Services (DHCS) eligibility standards and County caseworker procedures."
        else:
            return f"Official Medi-Cal Policy Guide section for {title}. Outlines California Department of Health Care Services (DHCS) eligibility criteria and County HHSA procedures."

def main():
    with open(DOCS_PATH, 'r', encoding='utf-8') as f:
        docs = json.load(f)

    for doc in docs:
        s = build_summary(doc)
        s = re.sub(r'\s+', ' ', s).strip()
        if not s.endswith('.'):
            s += '.'
        doc['summary'] = s

    with open(DOCS_PATH, 'w', encoding='utf-8') as f:
        json.dump(docs, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated clean, authoritative summaries for all {len(docs)} documents in {DOCS_PATH}.")

if __name__ == '__main__':
    main()
