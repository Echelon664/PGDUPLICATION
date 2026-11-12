import json

OFFICIAL_CW_SECTIONS = [
    ('10-001', 'Background', 'CalWORKs and Employment Services overview and legal authority'),
    ('10-002', 'Federal Work Participation Rate (WPR)', 'Federal work participation rate data reporting and verification'),
    ('10-005', 'Welfare-to-Work', 'WTW sequence, orientation, appraisal, assessments, activities, and teen rules'),
    ('10-006', 'Learning Disabilities', 'Learning disability evaluations and accommodations'),
    ('10-007', 'Family Stabilization', 'Intensive case management and stabilization services'),
    ('10-008', 'CalWORKs Housing Support Program', 'Housing identification, rent assistance, and case management'),
    ('10-009', 'Home Visiting Program', 'Voluntary home visiting services for pregnant women and families with young children'),
    ('10-010', 'Child Care', 'Stage One child care eligibility, provider rules, and payment processing'),
    ('10-011', 'Supportive Services', 'Transportation, work-related expenses, and behavioral health support'),
    ('10-020', 'Exemptions & Good Cause', 'WTW participation exemptions and good cause criteria'),
    ('10-025', 'Compliance Process', 'Noncompliance conciliation and sanction procedures'),
    ('10-030', 'Participants Rights', 'Grievance procedures, state hearings, and participant rights'),
    ('10-050', 'Community Service', 'Community service work experience placements and hours'),
    ('10-150', 'Subsidized Employment Programs', 'Expanded subsidized employment and wage-subsidy work experience'),
    ('10-160', 'Wrap Around', 'Coordinated wrap-around multi-agency family support services'),
    ('10-170', 'CalWORKs Outcomes and Accountability Review (Cal-OAR)', 'State performance measures and continuous quality improvement'),
    ('10-200', 'Refugee Services', 'Refugee employment services and coordination'),
    ('10-260', 'Document Capture Procedures for Employment Services Contractors', 'Electronic document imaging and contractor workflow requirements'),
    ('10-300', 'WTW Activity Documentation and Reporting Requirements', 'Activity logs, timesheets, and attendance verification'),
    ('15-000', 'Cal-Learn', 'Teen parent education requirements, case management, and bonuses/sanctions'),
    ('15-100', 'TIME ON AID', '60-month cumulative lifetime cash aid time limit and exemptions'),
    ('19-000', 'Confidentiality of Information & Records', 'Case record safeguarding and disclosure authorization'),
    ('20-000', 'Integrity', 'Fraud prevention, investigation, and child care program integrity'),
    ('22-000', 'Notifications', 'Timely and adequate Notices of Action (NOA) and verification requests'),
    ('40-100', 'Application and Redetermination', 'Intake, immediate need cash, SAR 7 recertification, and ICT'),
    ('40-125', 'Restoration of Aid', 'Aid restoration within 12 months following discontinuance'),
    ('40-183', 'CalWORKs Special Programs', 'ARC program, IPT, Extended CalWORKs for NMD, and reunification'),
    ('41-400', 'Deprivation', 'Parental absence, incapacity, unemployment (U-parent), or death'),
    ('41-500', 'Assistance Unit', 'Mandatory AU composition, caretaker relatives, and temporary absence'),
    ('42-100', 'Age-Immunization-School Attendance', 'Age limits, teen parenting, school attendance, and childhood immunization'),
    ('42-200', 'Property', 'Real and personal property limitations, motor vehicles, and exclusions'),
    ('42-400', 'Residence', 'County residence, state presence, and citizen/noncitizen status'),
    ('43-100', 'Responsible Relatives', 'Parental responsibility and unrelated adults residing in the home'),
    ('43-200', 'Child Support', 'Assignment of support rights and child support cooperation rules'),
    ('44-100', 'Income', 'Earned, unearned, excluded, and exempt income determinations'),
    ('44-200', 'Special Needs', 'Recurring, nonrecurring, pregnancy, and homeless assistance payments'),
    ('44-260', 'Annual Reporting (Child Only Cases)', 'AR/CO reporting rules for child-only assistance units'),
    ('44-270', 'Semi-Annual Reporting (SAR)', 'SAR 7 mid-period mandatory and voluntary reporting'),
    ('44-300', 'Benefit Payments', 'Beginning date of aid, MAP calculation, and issuance methods'),
    ('44-350', 'Overpayment-IPV-Underpayment', 'Overpayment budgeting, recoupment, IPV penalties, and corrective underpayments'),
    ('45-000', 'CalWORKs Questions and Answers', 'County eligibility and policy guidance clarification Q&As'),
    ('45-200', 'Resources and Desk Aids', 'Assistance standards, MAP charts, property limits, and desk aids'),
    ('69-205', 'Refugee Cash Assistance (RCA)', 'Federal RCA program eligibility, time limits, and budgeting'),
    ('70-100', 'Trafficking and Crime Victims Assistance Program (TCVAP)', 'State-funded cash and supportive services for eligible victims of crime')
]

SECTIONS_BY_CODE = {s[0]: s for s in OFFICIAL_CW_SECTIONS}

def update():
    docs_path = "/Users/echelon619/Desktop/ChrisPG/data/documents.json"
    with open(docs_path, "r", encoding="utf-8") as f:
        docs = json.load(f)

    cw_updated = 0
    for d in docs:
        if "CalWORKs" not in d.get("programs", []):
            continue

        ch = d.get("chapter", "")
        title = d.get("title", "")

        # Check for Special Notices
        if ch in ["2021", "2022", "2025", "2026"] or "SN " in title or "Special Notice" in title:
            d["section_num"] = title.split()[1] if title.startswith("SN ") else "SN"
            d["section_title"] = "Special Notices & Policy Bulletins"
            d["chapter"] = f"Special Notices & Policy Bulletins ({ch if ch.isdigit() else 'Updates'})"
            d["category"] = "Special Notices & Policy Bulletins"
            d["category_desc"] = "County Policy Bulletins, COLA notices, emergency directives, and annual adjustments"
            d["order"] = 99
            cw_updated += 1
            continue

        # Match to official section
        matched_code = None
        for code in SECTIONS_BY_CODE.keys():
            if ch.startswith(code):
                matched_code = code
                break

        if matched_code:
            code, sec_title, desc = SECTIONS_BY_CODE[matched_code]
            d["section_num"] = code
            d["section_title"] = sec_title
            d["chapter"] = f"{code} {sec_title}"
            d["category"] = f"{code} {sec_title}"
            d["category_desc"] = desc
            
            # Find index in OFFICIAL_CW_SECTIONS
            sec_idx = [s[0] for s in OFFICIAL_CW_SECTIONS].index(code) + 1
            d["order"] = sec_idx
            cw_updated += 1
        else:
            print(f"[!] Warning: Unmatched CalWORKs doc: {d['id']}, ch={ch}, title={title}")

    print(f"Updated {cw_updated} CalWORKs documents.")

    with open(docs_path, "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2)
    print("Saved to", docs_path)

if __name__ == "__main__":
    update()
