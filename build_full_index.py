import json, re, os, zlib, urllib.parse

pdf_dir = '/Users/echelon619/.gemini/antigravity/scratch/sd-benefits-search/data/pdfs'

def extract_pdf_bt_text(filepath):
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
    except:
        return ''
    out = []
    pos = 0
    while True:
        s = data.find(b'stream', pos)
        if s == -1:
            break
        s_start = data.find(b'\n', s)
        if s_start == -1:
            break
        s_start += 1
        e = data.find(b'endstream', s_start)
        if e == -1:
            break
        raw_stream = data[s_start:e].strip()
        pos = e + 9
        if not raw_stream:
            continue
        try:
            decomp = zlib.decompress(raw_stream)
        except:
            continue
        
        bt_pos = 0
        while True:
            bt_idx = decomp.find(b'BT', bt_pos)
            if bt_idx == -1:
                break
            et_idx = decomp.find(b'ET', bt_idx)
            if et_idx == -1:
                et_idx = len(decomp)
            block = decomp[bt_idx:et_idx]
            
            i = 0
            b_len = len(block)
            while i < b_len:
                if block[i:i+1] == b'(':
                    j = i + 1
                    paren = 1
                    buf = []
                    while j < b_len and paren > 0:
                        c = block[j:j+1]
                        if c == b'\\':
                            buf.append(block[j+1:j+2])
                            j += 2
                        elif c == b'(':
                            paren += 1
                            buf.append(b'(')
                            j += 1
                        elif c == b')':
                            paren -= 1
                            if paren > 0:
                                buf.append(b')')
                            j += 1
                        else:
                            buf.append(c)
                            j += 1
                    txt = b''.join(buf).decode('latin1', 'ignore').strip()
                    if txt:
                        out.append(txt)
                    i = j
                else:
                    i += 1
            bt_pos = et_idx + 2
    raw = ' '.join(out)
    return re.sub(r'\s+', ' ', raw).strip()

if __name__ == '__main__':
    tables_text = []
with open('/Users/echelon619/.gemini/antigravity/brain/df70e671-e6fb-4e6d-b828-18340155569b/.system_generated/logs/transcript_full.jsonl') as f:
    for line in f:
        data = json.loads(line)
        content = data.get('content', '')
        if 'COMPLETED / TASK_COMPLETED' in content and '| Index |' in content:
            tables_text.append(content)

available_pdfs = sorted(os.listdir(pdf_dir))

def normalize(name):
    return re.sub(r'[^a-z0-9]', '', name.lower())

all_entries = {}
for msg in tables_text:
    for line in msg.split('\n'):
        if line.startswith('|') and not line.startswith('| Index') and not line.startswith('| :---') and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 4:
                try:
                    idx = int(parts[0])
                except:
                    continue
                if len(parts) >= 6:
                    title = parts[1]
                    file_id = parts[2]
                    target_fn = parts[4].strip('`')
                else:
                    title = parts[2]
                    file_id = parts[3]
                    target_fn = f"{title.replace('/', '_')}.pdf"
                
                norm_target = normalize(target_fn.replace('.pdf', ''))
                norm_title = normalize(title)
                
                matched_pdf = None
                for fn in available_pdfs:
                    norm_fn = normalize(fn.replace('.pdf', ''))
                    if norm_fn == norm_target or norm_fn == norm_title:
                        matched_pdf = fn
                        break
                if not matched_pdf:
                    for fn in available_pdfs:
                        norm_fn = normalize(fn.replace('.pdf', ''))
                        if norm_fn.startswith(norm_title[:10]) or norm_title.startswith(norm_fn[:10]):
                            matched_pdf = fn
                            break
                if not matched_pdf:
                    prefix = title.split()[0]
                    for fn in available_pdfs:
                        if fn.startswith(prefix):
                            matched_pdf = fn
                            break
                
                all_entries[idx] = {
                    'index': idx,
                    'title': title,
                    'file_id': file_id,
                    'pdf_filename': matched_pdf or target_fn
                }

print(f'Building index for {len(all_entries)} CalFresh documents...')

def get_chapter(title):
    if title.startswith('SN') or title.startswith('25-'):
        return 'Special Notices'
    m = re.match(r'^(63-[0-9]+)', title)
    if not m:
        return 'General Policy'
    code = m.group(1)
    ch_map = {
        '63-100': '63-100 Application Process',
        '63-101': '63-100 Application Process',
        '63-103': '63-100 Application Process',
        '63-105': '63-100 Application Process',
        '63-107': '63-100 Application Process',
        '63-109': '63-100 Application Process',
        '63-113': '63-100 Application Process',
        '63-115': '63-100 Application Process',
        '63-117': '63-100 Application Process',
        '63-118': '63-100 Application Process',
        '63-120': '63-100 Application Process',
        '63-121': '63-100 Application Process',
        '63-123': '63-100 Application Process',
        '63-124': '63-100 Application Process',
        '63-125': '63-100 Application Process',
        '63-1100': '63-1100 Handbook',
        '63-1101': '63-1100 Handbook',
        '63-1103': '63-1100 Handbook',
        '63-150': '63-150 Non-Financial',
        '63-151': '63-150 Non-Financial',
        '63-152': '63-150 Non-Financial',
        '63-153': '63-150 Non-Financial',
        '63-154': '63-150 Non-Financial',
        '63-156': '63-150 Non-Financial',
        '63-157': '63-150 Non-Financial',
        '63-159': '63-150 Non-Financial',
        '63-161': '63-150 Non-Financial',
        '63-162': '63-150 Non-Financial',
        '63-166': '63-150 Non-Financial',
        '63-167': '63-150 Non-Financial',
        '63-168': '63-150 Non-Financial',
        '63-169': '63-150 Non-Financial',
        '63-200': '63-200 Resources',
        '63-201': '63-200 Resources',
        '63-203': '63-200 Resources',
        '63-220': '63-220 Income',
        '63-222': '63-220 Income',
        '63-223': '63-220 Income',
        '63-224': '63-220 Income',
        '63-225': '63-220 Income',
        '63-230': '63-230 Income Deductions',
        '63-231': '63-230 Income Deductions',
        '63-232': '63-230 Income Deductions',
        '63-233': '63-230 Income Deductions',
        '63-234': '63-230 Income Deductions',
        '63-235': '63-230 Income Deductions',
        '63-240': '63-240 Special Circumstances',
        '63-247': '63-240 Special Circumstances',
        '63-250': '63-250 Budgeting and Benefit Calculation',
        '63-251': '63-250 Budgeting and Benefit Calculation',
        '63-252': '63-250 Budgeting and Benefit Calculation',
        '63-254': '63-250 Budgeting and Benefit Calculation',
        '63-255': '63-250 Budgeting and Benefit Calculation',
        '63-270': '63-270 Semi-Annual Reporting',
        '63-271': '63-270 Semi-Annual Reporting',
        '63-272': '63-270 Semi-Annual Reporting',
        '63-274': '63-270 Semi-Annual Reporting',
        '63-280': '63-280 Mid-Period Reporting',
        '63-283': '63-280 Mid-Period Reporting',
        '63-287': '63-280 Mid-Period Reporting',
        '63-300': '63-300 Certification',
        '63-301': '63-300 Certification',
        '63-302': '63-300 Certification',
        '63-303': '63-300 Certification',
        '63-304': '63-300 Certification',
        '63-306': '63-300 Certification',
        '63-320': '63-320 Transitional CalFresh',
        '63-321': '63-320 Transitional CalFresh',
        '63-330': '63-330 CalFresh Expansion for SSI-SSP Recipients',
        '63-331': '63-330 CalFresh Expansion for SSI-SSP Recipients',
        '63-332': '63-330 CalFresh Expansion for SSI-SSP Recipients',
        '63-333': '63-330 CalFresh Expansion for SSI-SSP Recipients',
        '63-350': '63-350 Case Management',
        '63-351': '63-350 Case Management',
        '63-352': '63-350 Case Management',
        '63-353': '63-350 Case Management',
        '63-354': '63-350 Case Management',
        '63-355': '63-350 Case Management',
        '63-356': '63-350 Case Management',
        '63-357': '63-350 Case Management',
        '63-358': '63-350 Case Management',
        '63-359': '63-350 Case Management',
        '63-360': '63-360 Elderly Simplified Application Project (ESAP)',
        '63-370': '63-370 Minimum Nutrition Benefit (MNB) Pilot Program',
        '63-380': '63-380 Prepared Meal Programs',
        '63-420': '63-420 Work Incentive Nutrition Supplement (WINS)',
        '63-450': '63-450 Claims & Adjustments',
        '63-451': '63-450 Claims & Adjustments',
        '63-452': '63-450 Claims & Adjustments',
        '63-453': '63-450 Claims & Adjustments',
        '63-454': '63-450 Claims & Adjustments',
        '63-455': '63-450 Claims & Adjustments',
        '63-456': '63-450 Claims & Adjustments',
        '63-500': '63-500 Disaster CalFresh and Household Misfortune',
        '63-501': '63-500 Disaster CalFresh and Household Misfortune',
        '63-509': '63-500 Disaster CalFresh and Household Misfortune',
        '63-600': '63-600 Questions and Answers',
        '63-601': '63-600 Questions and Answers',
        '63-602': '63-600 Questions and Answers',
        '63-604': '63-600 Questions and Answers',
        '63-605': '63-600 Questions and Answers',
        '63-608': '63-600 Questions and Answers',
        '63-609': '63-600 Questions and Answers',
        '63-610': '63-600 Questions and Answers',
        '63-900': '63-900 CalFresh Work-Related Policy Areas',
        '63-901': '63-900 CalFresh Work-Related Policy Areas',
        '63-902': '63-900 CalFresh Work-Related Policy Areas',
        '63-903': '63-900 CalFresh Work-Related Policy Areas',
        '63-904': '63-900 CalFresh Work-Related Policy Areas',
        '63-905': '63-900 CalFresh Work-Related Policy Areas'
    }
    return ch_map.get(code, f'Chapter {code}')

documents = []
for idx in sorted(all_entries.keys()):
    entry = all_entries[idx]
    title = entry['title']
    file_id = entry['file_id']
    pdf_fn = entry['pdf_filename']
    full_path = os.path.join(pdf_dir, pdf_fn)
    
    extracted_text = extract_pdf_bt_text(full_path)
    if not extracted_text:
        extracted_text = f"Official San Diego County CalFresh Policy Document: {title}. File ID: {file_id}. Access local PDF for full text."
    
    chapter = get_chapter(title)
    
    doc = {
        'id': f"cf-{file_id}",
        'title': title,
        'chapter': chapter,
        'programs': ['CalFresh'],
        'published_on': '2026-01-01T00:00:00Z',
        'file_type': 'PDF',
        'local_pdf_url': f"/pdfs/{urllib.parse.quote(pdf_fn)}",
        'official_url': f"https://file.sandiegocounty.gov/HHSAPublicSite/View?FileId={file_id}",
        'content': extracted_text[:12000],
        'sections': [
            {'heading': chapter, 'text': extracted_text[:4000]}
        ]
    }
    documents.append(doc)

# CalWORKs & Medi-Cal
calworks_docs = [
    {
        'id': 'cw-448-main',
        'title': 'CalWORKs Program Guide: Overview & Eligibility Standards',
        'chapter': 'CalWORKs Policy',
        'programs': ['CalWORKs'],
        'published_on': '2026-01-01T00:00:00Z',
        'file_type': 'HTML',
        'local_pdf_url': 'https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=448',
        'official_url': 'https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=448',
        'content': 'CalWORKs (California Work Opportunity and Responsibility to Kids) provides cash aid and services to eligible families with children. San Diego County HHSA administers CalWORKs across welfare-to-work, childcare, and basic cash aid under Folder 448.',
        'sections': [{'heading': 'Overview', 'text': 'CalWORKs cash assistance and welfare-to-work requirements in San Diego County.'}]
    }
]

medical_docs = [
    {
        'id': 'mc-599-main',
        'title': 'Medi-Cal Policy Manual: MAGI & Non-MAGI Eligibility',
        'chapter': 'Medi-Cal Policy',
        'programs': ['Medi-Cal'],
        'published_on': '2026-01-01T00:00:00Z',
        'file_type': 'HTML',
        'local_pdf_url': 'https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=599',
        'official_url': 'https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=599',
        'content': 'Medi-Cal provides health care coverage to low-income children, adults, seniors, and persons with disabilities. Administered by San Diego County HHSA under Folder 599 including Modified Adjusted Gross Income (MAGI) and Non-MAGI guidelines.',
        'sections': [{'heading': 'Overview', 'text': 'Medi-Cal eligibility categories, application requirements, and renewal rules.'}]
    }
]

documents.extend(calworks_docs)
documents.extend(medical_docs)

out_path = '/Users/echelon619/.gemini/antigravity/scratch/sd-benefits-search/data/documents.json'
with open(out_path, 'w') as f:
    json.dump(documents, f, indent=2)

print(f'Successfully built {out_path} with {len(documents)} total documents ({len(all_entries)} original CalFresh policy files)!')
