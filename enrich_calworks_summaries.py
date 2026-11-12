#!/usr/bin/env python3
import json

DOCS_PATH = "/Users/echelon619/Desktop/ChrisPG/data/documents.json"

ENRICHED_CW_SUMMARIES = {
    # Special Notices & Policy Bulletins
    "cw-123": "SN 21-03 outlines caseworker procedures for identifying, reviewing, and processing suspected EDD unemployment insurance fraud and identity theft. Prohibits adverse CalWORKs grant reductions or case closures when clients are victimized by fraudulent 1099-G tax filings without independent corroboration.",
    "cw-124": "SN 21-06 establishes administrative procedures and verification standards for the CalWORKs 60-month lifetime time-on-aid limit good cause exemption. Grants clock-stopping exemptions for recipients facing severe barriers, domestic abuse, or circumstances beyond their control.",
    "cw-125": "SN 21-08 details policy guidelines on overpayments incurred during the COVID-19 pandemic state of emergency. Outlines administrative waiver criteria, compromised claim settlements, and a pause on non-fraud collection activities to prevent undue hardship on vulnerable families.",
    "cw-126": "SN 21-15 updates maximum Regional Market Rate (RMR) reimbursement ceilings for child care providers under subsidized CalWORKs Stage One child care. Directs caseworkers on payment adjustments and authorization notices for licensed and license-exempt providers.",
    "cw-127": "SN 22-02 details the implementation of Assembly Bill 79, which repealed the CalWORKs 48-month time-on-aid limit and established the expanded 60-month cumulative lifetime cash aid clock. Outlines automated CalWIN/CalSAWS clock tracking and notification procedures.",
    "cw-128": "SN 25-03 announces updated Income Reporting Threshold (IRT) tiers across assistance unit sizes effective October 2025. Directs caseworkers on mandatory mid-period income reporting rules when gross income exceeds the assigned IRT, and outlines effective dates for grant changes.",
    "cw-129": "SN 25-04 establishes updated CalWORKs monthly benefit standards, Maximum Aid Payment (MAP) levels, and income eligibility thresholds following the annual Social Security Title II Cost-of-Living Adjustment (COLA). Outlines automated mass update schedules in automated systems.",
    "cw-130": "SN 25-05 directs caseworkers on implementing California's statutory minimum wage increase. Outlines procedures for recalculating gross earned income, applying the $450 standard disregard and 50% earned income disregard, and adjusting Welfare-to-Work participation hours.",
    "cw-131": "SN 26-01 details annual mandatory client notification and outreach regarding the federal Earned Income Tax Credit (EITC), California Earned Income Tax Credit (CalEITC), and Young Child Tax Credit cash refunds, confirming that tax refunds are fully exempt from property and income budgeting.",
    "cw-132": "SN 26-02 publishes annual Cost-of-Living Adjustments (COLA) increasing the Minimum Basic Standard of Adequate Care (MBSAC) and Income-In-Kind (IIK) levels effective July 2026. Outlines applicant financial eligibility gross income test thresholds across family sizes.",
    "cw-133": "SN 26-03 provides policy instructions regarding the CalWORKs 60-month time limit exemption for adult recipients living in Indian Country where the unemployment rate exceeds 50%. Outlines tribal verification procedures and automated time-clock stopping in CalSAWS.",
    "cw-134": "SN 26-04 announces the annual statutory increase to the CalWORKs Maximum Aid Payment (MAP) levels effective October 2026 for both exempt and non-exempt assistance units across San Diego County (Region 1). Details automated payment adjustments and client notice mailings.",

    # Chapter 10-001: Background
    "cw-135": "Provides a comprehensive operational overview of CalWORKs eligibility and Welfare-to-Work (WTW) employment services under Assembly Bill 79. Details the repeal of the 48-month time limit in favor of the 60-month cumulative lifetime cash aid clock, the repeal of the WTW 24-month time clock, and core program goals centered on family stabilization, barrier removal, and career pathways toward permanent self-sufficiency.",

    # Chapter 10-002: WPR
    "cw-136": "Details federal Work Participation Rate (WPR) reporting requirements under TANF, sampling methodologies, countable hourly benchmarks, and county compliance performance measures. Outlines core work activities (employment, work experience, vocational training) and non-core activities needed to meet federal 50% all-families and 90% two-parent rate benchmarks.",

    # Chapter 10-005: Welfare-to-Work
    "cw-137": "Details the CalWORKs Welfare-to-Work (WTW) sequence and mandatory participation hours: 20 hours/week for single parents with a child under age 6, 30 hours/week for single parents with children age 6 and older, and 35 hours/week for two-parent assistance units. Outlines the mandatory flow from orientation and appraisal to assessment, plan creation, and ongoing activity tracking.",
    "cw-138": "Outlines core responsibilities of Employment Services Specialists (ESS) and contracted case managers. Details duty assignments including assessing job readiness, executing supportive service payments, monitoring monthly attendance logs, coordinating with eligibility workers, and initiating timely conciliation prior to sanction.",
    "cw-139": "Governs the mandatory Welfare-to-Work orientation and appraisal process. Evaluates client work history, educational attainment, vocational skills, and immediate supportive service needs (child care, transportation). Mandates screening for domestic violence, mental health, substance use, and learning disabilities during initial engagement.",
    "cw-140": "Details CalWORKs WTW initial engagement activities, orientation attendance scheduling, barrier screening, and sequencing toward formal appraisal. Outlines caseworker actions when an individual fails to attend scheduled engagement appointments, ensuring good cause is evaluated before issuing noncompliance notices.",
    "cw-141": "Governs comprehensive vocational assessment and reassessment for WTW participants not readily employable. Evaluates employment history, educational aptitude, career interests, local labor market conditions, and supportive service needs to formulate a realistic, structured pathway to family-supporting wages.",
    "cw-142": "Details the development of the individualized Welfare-to-Work Employment Services Plan (Form WTW 2). Outlines allowable assigned activities, weekly scheduled hours, supportive service authorizations (child care, mileage, transit passes), participant rights, and mandatory 30-day reassessment criteria.",
    "cw-143": "Specifies approved Welfare-to-Work activities: unsubsidized employment, subsidized private/public sector jobs, work experience, on-the-job training, job search and readiness, vocational education, community service, and education directly related to employment. Defines hourly participation limits and tracking protocols.",
    "cw-144": "Governs case transfers and returns between County HHSA Family Resource Centers (FRCs) and contracted employment services providers. Details electronic file transfer protocols, tracking participant relocations across regional service areas, and ensuring uninterrupted supportive service payments.",
    "cw-145": "Outlines specialized employment services participation and education requirements for pregnant and parenting teens. Details integration with the Cal-Learn program, school attendance mandates, child care arrangements, and transition into adult WTW services upon reaching age 19.",

    # Chapter 10-006: Learning Disabilities
    "cw-146": "Governs learning disabilities screening and formal evaluation (EVA) for Welfare-to-Work participants. Screening is offered at appraisal, assessment, or upon participant request. Clients with identified learning disabilities receive workplace accommodations, specialized vocational training modifications, and reduced hourly participation targets tailored to their evaluation.",

    # Chapter 10-007: Family Stabilization
    "cw-147": "Details the CalWORKs Family Stabilization (FS) program providing intensive case management and specialized barrier removal funds for families in immediate crisis. Authorizes flexible barrier removal funds for emergency housing, utility arrears, domestic violence safety, mental health crisis support, and substance use stabilization.",

    # Chapter 10-008: Housing Support Program (HSP)
    "cw-148": "Governs the CalWORKs Housing Support Program (HSP) assisting homeless families or families at imminent risk of homelessness. Authorizes evidence-based rapid re-housing services, including housing identification, move-in assistance, security deposits, temporary rental subsidies, and intensive housing case management.",

    # Chapter 10-009: Home Visiting Program
    "cw-149": "Details the voluntary CalWORKs Home Visiting Program (HVP) connecting pregnant individuals and families with children under age 24 months to registered nurses or trained home visitors. Outlines child health screenings, developmental milestones, positive parenting guidance, and family wellness support.",

    # Chapter 10-010: Child Care
    "cw-150": "Provides a comprehensive overview of CalWORKs Stage One child care administered by County HHSA and child care contractors. Assists current and former CalWORKs recipients with child care payments while participating in approved WTW activities, employment, or Cal-Learn education.",
    "cw-151": "Establishes CalWORKs Stage One child care eligibility criteria, ensuring continuous care authorization for 12 months. Covers children under age 13 (or up to age 21 if physically/mentally incapacitated or under court supervision), and details transition to Stage Two after 24 months of cash aid discontinuance.",
    "cw-152": "Specifies child care provider requirements, authorizing parent choice among licensed child care centers, licensed family child care homes, and license-exempt relative caregivers. Details mandatory TrustLine background clearances and health/safety self-certification for exempt providers.",
    "cw-153": "Governs caseworker procedures for approving or denying Stage One child care requests, executing Form CCP 7 parent/provider contracts, establishing authorized care hours based on work/activity schedules, and setting enrollment effective dates.",
    "cw-154": "Details child care payment methodologies and Regional Market Rate (RMR) ceilings. Covers provider reimbursement processing, monthly child care attendance invoices, payment calculation for full-time and part-time care, and handling registration fee reimbursements.",
    "cw-155": "Establishes legal standards for Child Care Notices of Action (NOA). Directs that adverse actions (changes in care hours, copayments, or terminations) must be mailed at least 10 calendar days prior to the effective date, detailing appeal rights and aid-paid-pending provisions.",
    "cw-156": "Governs general child care program administration, provider payment reconciliation, resolving child care attendance discrepancies, and managing child care contractor operational coordination across San Diego County.",

    # Chapter 10-011: Supportive Services
    "cw-157": "Governs Welfare-to-Work supportive services, including transportation reimbursements (public transit passes, mileage reimbursement for private vehicles), ancillary work-related expenses (books, tools, uniforms, licensing fees), and child care support necessary for participation.",
    "cw-158": "Outlines behavioral health services integrated within CalWORKs, providing direct access to county mental health clinicians and substance use disorder treatment specialists to identify and address barriers impacting family stability and employment readiness.",

    # Chapter 10-020: Exemptions & Good Cause
    "cw-159": "Details statutory Welfare-to-Work participation exemptions: parent caring for a child under 12 months (one-time lifetime exemption), medical incapacity verified by Form CW 61, primary caregiver for an incapacitated household member, advanced age (60+), or domestic violence.",
    "cw-160": "Establishes good cause criteria for temporary absence or failure to participate in scheduled WTW activities. Valid reasons include verified short-term personal or family illness, lack of licensed or affordable child care, temporary transportation breakdown, or severe family emergencies.",

    # Chapter 10-025: Compliance Process
    "cw-161": "Governs the Welfare-to-Work noncompliance conciliation process. When an unexcused absence occurs, the county must issue Form NA 840 (Cause Determination Notice) initiating a 20-calendar-day conciliation period to establish good cause, negotiate a compliance plan, or cure sanctions before cash grant reductions occur.",

    # Chapter 10-030: Participants Rights & State Hearings
    "cw-162": "Details participant rights to formal grievance procedures and administrative dispute resolution when a participant disagrees with an Employment Services Specialist decision, assigned WTW activity, or denial of supportive service payments.",
    "cw-163": "Governs sanction imposition and state fair hearing rules. When conciliation fails, the noncompliant adult's financial needs are removed from the CalWORKs cash grant. Outlines sanction cure procedures (re-engaging in the activity for 30 days or signing an agreement) and aid-paid-pending rules.",

    # Chapter 10-050 to 10-300: Specialized WTW Programs
    "cw-164": "Governs Community Service and work experience placements for WTW participants who have not found unsubsidized employment. Outlines public and nonprofit agency work sites, maximum allowable hours determined by dividing the cash grant by minimum wage, and skills development.",
    "cw-165": "Details the Expanded Subsidized Employment (ESE) program providing wage subsidies to private and nonprofit employers hiring CalWORKs participants. Covers subsidy tiers, 6-month placement duration, employer agreements, and transition into permanent unsubsidized employment.",
    "cw-166": "Governs the Expanded Work Experience program, providing structured, non-paid work experience assignments with public and community-based organizations to develop foundational workplace skills, references, and professional experience.",
    "cw-167": "Outlines the multi-agency Wraparound service model for CalWORKs families experiencing complex, co-occurring challenges (child welfare involvement, housing crisis, trauma). Details family team conferencing and customized supportive interventions.",
    "cw-168": "Details the CalWORKs Outcomes and Accountability Review (Cal-OAR) framework, establishing continuous quality improvement (CQI) metrics, state performance measures, customer engagement surveys, and local county improvement plans.",
    "cw-169": "Governs Refugee Employment Services (RES) tailored to newly arrived refugees, asylees, and human trafficking victims receiving CalWORKs. Outlines coordination with resettlement agencies, vocational English as a Second Language (VESL), and culturally competent job placement.",
    "cw-170": "Establishes electronic document imaging and capture standards for Employment Services contractors, detailing secure uploading, mandatory metadata indexing, case record retention, and quality assurance protocols.",
    "cw-171": "Details mandatory Welfare-to-Work activity documentation and verification standards. Outlines monthly attendance logs, employer timesheets, school progress reports, and caseworker data entry deadlines in CalSAWS to maintain WPR compliance.",

    # Chapter 15-000: Cal-Learn
    "cw-172": "Introduces the Cal-Learn program, a mandatory statewide program for pregnant and parenting teens under age 19 receiving CalWORKs cash aid who have not yet earned a high school diploma or equivalent.",
    "cw-173": "Establishes Cal-Learn eligibility, mandatory participation criteria, and exemption rules (illness, lack of child care). Teens must remain enrolled in an accredited secondary education program, maintain regular attendance, and submit quarterly report cards.",
    "cw-174": "Governs Cal-Learn orientation and referral workflows from CalWORKs eligibility workers to specialized adolescent case managers. Details explaining rights, responsibilities, report card bonus/sanction rules, and supportive service entitlements.",
    "cw-175": "Details Cal-Learn supportive services, providing guaranteed child care assistance, transportation reimbursements (transit passes, mileage), and educational expenses (textbooks, lab fees, graduation cap and gown costs).",
    "cw-176": "Governs intensive adolescent case management services under Cal-Learn. Case managers assist teen parents with academic planning, prenatal and pediatric health care, housing stability, and parenting skills development.",
    "cw-177": "Establishes good cause criteria for Cal-Learn participants experiencing academic or attendance difficulties, protecting teen parents from financial penalties when setbacks result from postpartum complications, infant illness, or domestic challenges.",
    "cw-178": "Governs the application of Cal-Learn financial bonuses and sanctions: a $100 cash bonus for each quarterly report card showing satisfactory progress (C average or better), a $500 bonus for high school graduation, and a $100 grant reduction sanction for failing grades or unexcused school non-attendance.",

    # Chapter 15-100: Time on Aid
    "cw-179": "Details the 60-month cumulative lifetime cash aid time-on-aid limit for adult CalWORKs recipients. Outlines automated CalSAWS tracking, counting out-of-state TANF months, and statutory clock-stopping exemptions for disability, domestic violence, advanced age (60+), or caring for an ill family member.",

    # Chapter 19-000 to 22-000: Administrative Provisions
    "cw-180": "Establishes strict confidentiality standards safeguarding CalWORKs public assistance case files under California Welfare and Institutions Code Section 10850. Restricts disclosure of records, addresses client consent authorizations, and defines exceptions for law enforcement and official audits.",
    "cw-181": "Governs customer rights to request and obtain copies of information contained within their CalWORKs case files. Details caseworker response timeframes, photo identification verification, and redaction of privileged confidential records.",
    "cw-182": "Outlines early fraud prevention, detection, and investigation criteria. Details referral thresholds to the Special Investigations Unit (SIU), home visit guidelines, applicant due process protections, and preventing improper benefit issuance.",
    "cw-183": "Governs child care program integrity and fraud prevention within CalWORKs Stage One child care. Details provider billing audits, attendance sheet verification, unannounced provider site visits, and recovering child care overpayments.",
    "cw-184": "Establishes legal standards for CalWORKs Notices of Action (NOA), requiring that adverse action notices provide 10-day advance notice, state the specific factual and legal basis, include grant calculation worksheets, and explain hearing rights.",
    "cw-185": "Governs Form CW 2200 verification request protocols. When additional documentation is needed, caseworkers must issue Form CW 2200 providing the customer at least 10 calendar days to comply, and must offer agency assistance to obtain required third-party records.",

    # Chapter 40-100: Application and Redetermination
    "cw-186": "Details CalWORKs application intake, filing rights, acceptable written, electronic, and telephonic signatures, and the mandatory 45-day processing standard from application submission to final approval or denial.",
    "cw-187": "Governs initial face-to-face or telephonic application interviews, evaluating deprivation factors, Assistance Unit composition, household resources, and immediate supportive service needs.",
    "cw-188": "Establishes procedures for Immediate Need emergency cash assistance: up to $200 issued within 1 business day for households facing immediate eviction, lack of food, or utility shutoff, prior to completing full eligibility verifications.",
    "cw-189": "Governs annual redetermination (RD) procedures for ongoing CalWORKs cases, detailing submission of Form SAWS 2 Plus, scheduling redetermination interviews, verifying ongoing income/property eligibility, and issuing timely renewal notices.",
    "cw-190": "Outlines the statutory Beginning Date of Aid (BDA) for CalWORKs cash assistance: benefits are calculated from the date of application or the date all eligibility conditions are met, ensuring prompt financial support for qualifying families.",
    "cw-191": "Specifies verification standards and acceptable documentation for CalWORKs intake, redeterminations, and mid-period changes, requiring electronic database verification attempts before requesting physical papers from clients.",
    "cw-192": "Governs the resolution of discrepant or conflicting information, distinguishing unintentional household reporting discrepancies from intentional misrepresentation, and detailing caseworker collateral contact standards.",
    "cw-193": "Governs CalWORKs Intercounty Transfers (ICT) when a family moves between California counties. Directs the sending county to transfer case records within 7 days and continue cash aid for 30 days while the receiving county assumes case management.",
    "cw-194": "Establishes caseworker procedures for case denials and voluntary withdrawals, detailing mandatory 30-day restoration rules without a new application if missing verifications are provided within 30 days of denial.",

    # Chapter 40-125: Restoration of Aid
    "cw-195": "Governs expedited restoration of aid for families whose CalWORKs cash assistance was discontinued within the prior 12 months, allowing resumption of benefits without repeating initial deprivation and resource evaluations.",

    # Chapter 40-183: CalWORKs Special Programs
    "cw-196": "Details the Approved Relative Caregiver (ARC) funding program providing cash aid equal to the basic foster care rate for eligible children placed with relative caregivers who are not eligible for federal Title IV-E foster care payments.",
    "cw-197": "Governs Extended CalWORKs for Non-Minor Dependents (NMDs) aged 18 through 20 who meet federal participation criteria (completing high school, postsecondary education, vocational training, or participating in employment activities).",
    "cw-198": "Details CalWORKs cash assistance and supportive services for parents participating in court-ordered Child Welfare Family Reunification plans, allowing ongoing grant payments for up to 180 days while children are temporarily placed in foster care.",
    "cw-199": "Governs Special Programs case budgeting and accounting, reconciling state and federal aid codes across ARC, NMD, and Family Reunification assistance units in automated eligibility systems.",
    "cw-200": "Establishes caseworker operational guidelines for Special Programs redeterminations, periodic reporting, and monitoring ongoing eligibility compliance across specialized child welfare and non-minor dependent cases.",

    # Chapter 41-400: Deprivation
    "cw-201": "Introduces statutory parental deprivation requirements for CalWORKs: children must be deprived of parental support or care due to parental death, continued absence, physical or mental incapacity, or parental unemployment (U-parent).",
    "cw-202": "Details parental deprivation based on continued absence, defining absence criteria (divorce, desertion, separation, incarceration) and establishing child support cooperation and referral requirements.",
    "cw-203": "Governs deprivation based on parental physical or mental incapacity. Outlines medical verification standards on Form CW 61, evaluating impairment expected to last at least 30 days and significantly reduce parental earning ability.",
    "cw-204": "Establishes deprivation criteria based on parental unemployment (U-Parent case). Outlines work history requirements, primary earner criteria, and the 100-hour employment limitation rule for applicant two-parent families.",
    "cw-205": "Governs deprivation based on parental death, acceptable death verification records (vital statistics, obituary, funeral home records), and surviving parent assistance unit budgeting.",

    # Chapter 41-500: Assistance Unit (AU)
    "cw-206": "Defines the Assistance Unit (AU), the group of persons within a household eligible to receive CalWORKs cash aid together, and details mandatory inclusion rules for eligible children, siblings, and natural/adoptive parents.",
    "cw-207": "Specifies optional AU members, excluded individuals (fleeing felons, undocumented noncitizens, sanctioned persons), and the distinction between the Assistance Unit and the Family Budget Unit (FBU).",
    "cw-208": "Governs caretaker relative eligibility when children reside with non-parent relatives (grandparents, aunts, uncles), detailing non-needy caretaker relative grant options versus needy caretaker inclusion.",
    "cw-209": "Details temporary absence rules, permitting children or adult AU members to remain on the CalWORKs grant during temporary absences of up to 30 days (or up to 180 days for medical treatment, education, or family reunification).",
    "cw-210": "Outlines multi-family household budgeting rules when multiple assistance units or non-AU individuals share a single residence, detailing shelter expense sharing and income isolation.",
    "cw-211": "Governs AU composition changes resulting from newborn births, custody transfers, or family member departures, outlining effective dates for grant adjustments and mid-period reporting timeframes.",
    "cw-212": "Details Assistance Unit classification codes, Federal TANF versus State-only aid types, and automated case setup rules in CalSAWS.",
    "cw-213": "Outlines caseworker operational procedures for resolving disputed AU composition claims and coordinating cross-program assistance units with CalFresh and Medi-Cal.",

    # Chapter 42-100: Age, Immunization, School Attendance
    "cw-214": "Establishes age eligibility limits: children are eligible through age 17, or through age 18 if enrolled full-time in high school and expected to graduate before age 19. Details Non-Minor Dependent extensions through age 20.",
    "cw-215": "Governs mandatory preschool immunization verification for children under age 6, requiring proof of age-appropriate vaccinations within 30 days of application, and detailing financial penalty exceptions for good cause.",
    "cw-216": "Establishes mandatory school attendance requirements for children aged 6 through 15, directing that failure to maintain regular attendance without good cause results in removing the child's needs from the cash grant.",

    # Chapter 42-200: Property Limits
    "cw-217": "Establishes allowable property limits for CalWORKs: $11,634 for standard assistance units, and $15,873 for households with a member who is disabled or age 60 and older. Property limits are adjusted annually for inflation.",
    "cw-218": "Distinguishes between real property (land, buildings, mineral rights) and personal property (bank accounts, vehicles, cash, stocks), detailing evaluation methodologies for liquid and non-liquid assets.",
    "cw-219": "Specifies countable property items that must be evaluated toward the asset limit, including checking/savings accounts, cryptocurrency, trust funds, promissory notes, and recreational vehicles.",
    "cw-220": "Details exempt resources excluded from property evaluation: household furnishings, personal effects, tools of a trade necessary for employment, tax-favored retirement accounts, 529 college savings, and EITC tax refunds.",
    "cw-221": "Governs temporary real property exemptions, allowing families owning non-exempt real property up to 9 months of conditional cash aid while actively attempting to sell the property at market value.",
    "cw-222": "Details Net Market Value (NMV) calculation procedures for personal and real property, subtracting verified encumbrances, liens, and outstanding debts from gross fair market value.",
    "cw-223": "Governs restricted accounts, allowing CalWORKs recipients to accumulate up to $10,000 in dedicated savings accounts for purchasing a home, starting a business, or paying higher education costs without impacting property eligibility.",
    "cw-224": "Establishes the absolute property exclusion for the family's primary residence, ensuring that the home owned and occupied by the Assistance Unit is completely exempt regardless of fair market value or equity.",
    "cw-225": "Governs motor vehicle property evaluation. Excludes the primary vehicle used for employment or transportation, applies a statutory $9,500 Fair Market Value disregard to additional vehicles, and exempts vehicles with equity under statutory caps.",

    # Chapter 42-400: Residence & Citizenship
    "cw-226": "Establishes California residency requirements: applicants must physically reside in California with the intent to remain permanently. Prohibits durational residency requirements and ensures unhoused individuals satisfy residence rules.",
    "cw-227": "Governs temporary absences from California, permitting continued cash aid for up to 30 days during out-of-state visits, and outlines procedures when a family moves permanently out of state.",
    "cw-228": "Specifies mandatory citizenship verification, eligible U.S. citizenship documents, and confirmation that citizen children residing with noncitizen parents remain fully eligible for CalWORKs cash aid.",
    "cw-229": "Establishes eligible noncitizen classifications for CalWORKs: Lawful Permanent Residents (LPRs), refugees, asylees, parolees, Cuban/Haitian entrants, and victims of human trafficking holding T-visas.",
    "cw-230": "Governs CalWORKs cash aid eligibility for battered noncitizens under the Violence Against Women Act (VAWA), detailing prima facie determination standards and protection from public charge concerns.",
    "cw-231": "Outlines sponsor deeming rules for sponsored immigrants, calculating countable sponsor income and resources toward the noncitizen's budget, and establishing indigent and domestic battery exemptions.",

    # Chapter 43-100: Responsible Relatives
    "cw-232": "Defines the financial and legal responsibility of parents to support their natural or adopted minor children, and establishes the scope of relative responsibility under California public assistance law.",
    "cw-233": "Governs Unrelated Adults in the Home (UAH), evaluating financial contributions for shelter and food, and calculating income-in-kind deductions when an unrelated adult cohabits with a caretaker parent.",

    # Chapter 43-200: Child Support
    "cw-234": "Governs mandatory assignment of child support rights to the state as a condition of receiving CalWORKs, and outlines cooperation requirements with the Department of Child Support Services (DCSS) to establish paternity and child support orders.",
    "cw-235": "Details child support non-cooperation penalties: refusal to cooperate with DCSS without good cause results in removing the non-cooperating parent's financial needs from the CalWORKs cash grant.",
    "cw-236": "Establishes good cause exemptions from child support cooperation, protecting parents when cooperation is anticipated to result in physical or emotional harm to the parent or child, or in cases of rape or incest.",
    "cw-237": "Governs child support collections and pass-through payments: the family receives the first $100 per month of collected child support for one child ($200 per month for two or more children) without reducing their CalWORKs grant.",

    # Chapter 44-100: Income
    "cw-238": "Establishes CalWORKs income eligibility tests: gross income is tested against the Minimum Basic Standard of Adequate Care (MBSAC), and net income is compared against the Region 1 Maximum Aid Payment (MAP) level.",
    "cw-239": "Details general income budgeting principles, converting weekly and biweekly pay to monthly gross amounts, evaluating earned versus unearned income, and determining reasonably anticipated income.",
    "cw-240": "Identifies exempt and non-countable income: federal student aid, loans, energy assistance, educational scholarships, foster care payments, and lump-sum tax credits (CalEITC, federal EITC).",
    "cw-241": "Governs the budgeting and verification of Unemployment Insurance Benefits (UIB) as countable unearned income, including automated EDD data cross-matching and grant adjustments.",
    "cw-242": "Details Unrelated Adult Contributions (UAC) and boarder/roomer income budgeting, calculating verified rental contributions toward the Assistance Unit's shelter expenses.",
    "cw-243": "Governs Income-In-Kind (IIK) budgeting when housing, utilities, or food are provided free of charge by an outside party, applying standardized IIK deduction values against the grant.",
    "cw-244": "Details automated data matches through the Income and Eligibility Verification System (IEVS), resolving wage and benefit discrepancies within 45 days to prevent improper payments.",

    # Chapter 44-200: Special Needs
    "cw-245": "Governs recurring special needs payments: special dietary allowances for verified medical conditions, transportation for ongoing medical treatment, and non-dietary maintenance allowances.",
    "cw-246": "Details nonrecurring special needs payments for catastrophic emergencies, natural disasters, and urgent domestic crises threatening family health and safety.",
    "cw-247": "Governs the Pregnancy Special Need (PSN) payment: a monthly supplemental cash benefit ($47 per month) issued to pregnant CalWORKs recipients from the date pregnancy is medically verified through birth.",
    "cw-248": "Provides an overview of CalWORKs Homeless Assistance (HA) for eligible families who are homeless or at imminent risk of eviction. Details temporary shelter assistance and permanent housing assistance.",
    "cw-249": "Governs Temporary Homeless Assistance, providing up to 16 consecutive calendar days of emergency shelter/motel funding while the family actively searches for permanent housing.",
    "cw-250": "Governs Permanent Homeless Assistance, providing financial assistance up to $2,500 to secure permanent housing (covering security deposits and last month's rent), or up to 2 months of verified rent arrears to prevent eviction.",
    "cw-251": "Details Expanded Temporary Homeless Assistance, providing additional temporary shelter nights for families facing domestic abuse, natural disasters, or specialized housing transition plans.",

    # Chapter 44-260 to 44-270: Reporting Systems
    "cw-252": "Governs the Annual Reporting/Child-Only (AR/CO) system for assistance units where no eligible adult is included in the grant (e.g., undocumented parents, non-needy caretakers), requiring only one redetermination report every 12 months.",
    "cw-253": "Establishes California's Semi-Annual Reporting (SAR) system for CalWORKs. Outlines household requirements to submit an Eligibility Status Report (Form SAR 7) every 6 months to maintain cash assistance.",
    "cw-254": "Details SAR income eligibility and prospective budgeting, calculating anticipated monthly income over the upcoming 6-month payment period using the $450 standard disregard and 50% earned income disregard.",
    "cw-255": "Establishes mandatory mid-period reporting triggers: households must report within 10 calendar days when gross income exceeds the Income Reporting Threshold (IRT), when an adult WTW participant moves, or when an individual joins the home.",
    "cw-256": "Governs voluntary mid-period reporting: households may report decreased income, increased family size, or special needs at any time, and the county must take action to increase the cash grant effective the following month.",
    "cw-257": "Governs county-initiated actions and third-party information updates during the SAR payment period, outlining specific criteria where the county is legally permitted to adjust grants without a client report.",

    # Chapter 44-300: Benefit Payments
    "cw-258": "Governs vendor payments, authorizing direct county payment of rent or utility subsidies to third-party landlords or utility providers when adult recipients demonstrate financial mismanagement.",
    "cw-259": "Details benefit issuance methods: direct electronic funds transfer into client bank accounts, Electronic Benefit Transfer (EBT) card access, and emergency warrant issuance.",
    "cw-260": "Establishes the Beginning Date of Aid (BDA) calculation, determining the exact calendar day cash assistance commences based on application filing and eligibility completion.",
    "cw-261": "Details grant calculation worksheets and payment determination, subtracting net countable income from the Region 1 Maximum Aid Payment (MAP) to calculate monthly cash benefits.",
    "cw-262": "Governs the Voluntary Maximum Aid Payment (MAP) Exclusion, allowing families with multiple children to exclude an individual from the grant to avoid exceeding maximum assistance standards.",

    # Chapter 44-350: Overpayment, IPV, Underpayment
    "cw-263": "Defines CalWORKs overpayments, establishing county responsibilities to identify, calculate, and establish claims for cash aid received in excess of the amount the assistance unit was legally entitled to receive.",
    "cw-264": "Provides regulatory definitions distinguishing Administrative Error (AE), Inadvertent Household Error (IHE), and Intentional Program Violation (IPV) overpayments.",
    "cw-265": "Governs overpayment investigation procedures, reviewing case files, reconciling historical payroll records, and documenting overissuance calculations.",
    "cw-266": "Details Aid Paid Pending rules when a customer files a timely state fair hearing request challenging an adverse grant reduction or termination, ensuring benefits continue until the hearing decision is rendered.",
    "cw-267": "Outlines overpayment recovery methods: active cases are recouped via monthly grant reduction (standard 10% reduction or 5% for administrative error), and inactive cases are collected via repayment agreements and tax refund intercepts.",
    "cw-268": "Details mathematical overpayment calculation worksheets, comparing aid actually paid against correct prospective grant entitlements for each affected calendar month.",
    "cw-269": "Governs overpayment recovery coordination between County HHSA, revenue collection units, and state agencies, ensuring statutory collection limits are respected.",
    "cw-270": "Establishes mandatory inclusion rules and overpayment debt liability for adult members who were part of the Assistance Unit when the overissuance occurred.",
    "cw-271": "Details the overpayment recomputation method, recalculating net claims after accounting for allowable earned income disregards that would have applied had the income been timely reported.",
    "cw-272": "Governs Intentional Program Violation (IPV) determinations: requires formal administrative disqualification hearings or court convictions, imposing mandatory 6-month, 12-month, or permanent individual cash aid disqualifications.",
    "cw-273": "Governs underpayments: when the county underpays an Assistance Unit due to administrative error or delayed action, the county must issue a corrective retroactive supplemental payment immediately.",
    "cw-274": "Details overpayments and underpayments in Employment Services supportive services (child care, mileage, transportation passes), outlining recovery and adjustment workflows.",
    "cw-275": "Governs the debt discharge process, establishing criteria for writing off and terminating collection efforts on uncollectible, cost-ineffective, or delinquent overpayment debts after 3 years.",

    # Chapter 45-000: Questions and Answers
    "cw-276": "Official County HHSA handbook resolving caseworker policy questions regarding Non-Minor Dependents (NMDs age 18-20), school attendance verifications, and benefit budgeting.",
    "cw-277": "Official County HHSA handbook resolving policy questions on Annual Reporting/Child-Only (AR/CO) cases, simplified redetermination workflows, and non-parent caretaker grant calculations.",

    # Chapter 45-200: Desk Aids
    "cw-278": "Comprehensive desk aid listing all CalWORKs state and federal aid codes (TANF, Safety Net, Child-Only, Special Medical) and automated system charging codes in CalSAWS.",
    "cw-279": "Official CalWORKs Assistance Standards Chart publishing Region 1 Maximum Aid Payment (MAP) levels for exempt and non-exempt units, MBSAC income levels, and standard disregards.",
    "cw-280": "Desk aid publishing current personal and real property limits ($11,634 standard / $15,873 disabled/elderly) and motor vehicle equity evaluation worksheets.",
    "cw-281": "Official CalWORKs Proration Chart providing daily proration factors for calculating partial-month cash aid grants based on the Beginning Date of Aid.",
    "cw-282": "Desk aid listing state Foster Care and Approved Relative Caregiver (ARC) basic monthly reimbursement rates across child age tiers.",
    "cw-283": "Desk aid detailing the treatment of Reception and Placement (R&P) cash grants provided to newly arrived refugees, detailing income exclusions and CalWORKs coordination.",
    "cw-284": "Official desk aid charting SAR 7 submit months, data months, and 6-month payment cycle schedules across all 12 calendar birth/application months.",
    "cw-285": "Desk aid detailing the evaluation and exclusion of federal, state, and private student loans, educational grants, and work-study earnings from CalWORKs income and property tests.",

    # Chapter 69-205 & 70-100: Specialized Cash Assistance
    "cw-286": "Governs the Refugee Cash Assistance (RCA) program providing monthly cash aid for up to 12 months to newly arrived refugees, asylees, and Cuban/Haitian entrants who do not have dependent children and are ineligible for CalWORKs. Mandates participation in employment services.",
    "cw-287": "Governs the state-funded Trafficking and Crime Victims Assistance Program (TCVAP), providing cash assistance, food assistance, and supportive employment services to noncitizen victims of human trafficking, domestic violence, or serious crimes while pursuing federal T-visas or U-visas."
}

def main():
    with open(DOCS_PATH, 'r', encoding='utf-8') as f:
        docs = json.load(f)

    updated_count = 0
    for d in docs:
        if 'CalWORKs' not in d.get('programs', []):
            continue
        cid = d.get('id', '')
        if cid in ENRICHED_CW_SUMMARIES:
            d['summary'] = ENRICHED_CW_SUMMARIES[cid]
            updated_count += 1
        else:
            print(f"Warning: No enriched summary for {cid} ({d.get('title')})")

    print(f"Updated {updated_count} CalWORKs summaries with enriched, verified PDF descriptions.")

    with open(DOCS_PATH, 'w', encoding='utf-8') as f:
        json.dump(docs, f, indent=2, ensure_ascii=False)

    print("Saved updated documents.json.")

if __name__ == '__main__':
    main()