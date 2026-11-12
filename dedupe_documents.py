#!/usr/bin/env python3
import json, re, hashlib, os, shutil

DATA_DIR = "/Users/echelon619/Desktop/ChrisPG/data"
DOCS_PATH = os.path.join(DATA_DIR, "documents.json")
BACKUP_PATH = os.path.join(DATA_DIR, "documents.backup.json")

shutil.copyfile(DOCS_PATH, BACKUP_PATH)
print(f"Backed up documents.json to {BACKUP_PATH}")

with open(DOCS_PATH, 'r', encoding='utf-8') as f:
    docs = json.load(f)

print(f"Original total documents: {len(docs)}")

def normalize_title(t):
    t = re.sub(r'\.(docx|doc|pdf)$', '', t, flags=re.I)
    return re.sub(r'[^a-z0-9]', '', t.lower())

def extract_section_code(title):
    m = re.match(r'^(63-\d+[a-z]?|SN[_\s]*[\d\-]+|[A-Z]\.\s+[^,\-]+|Section[_\s]*\d+)', title, re.IGNORECASE)
    if m:
        return re.sub(r'[^a-z0-9]', '', m.group(1).lower())
    return None

def clean_title(title):
    # Remove file extensions like .docx or .doc
    t = re.sub(r'\.(docx|doc|pdf)$', '', title, flags=re.I).strip()
    # Replace single or repeated underscores with spaces if it's an underscored title
    if '_' in t:
        t = re.sub(r'_+', ' ', t).strip()
    # Normalize multiple spaces
    t = re.sub(r'\s+', ' ', t).strip()
    # Fix typos like 'Applicaiton' -> 'Application'
    t = t.replace('Applicaiton', 'Application')
    return t

# Clean up all titles first
for d in docs:
    d['title'] = clean_title(d['title'])

# Perform duplicate detection per program
clean_docs = []
for prog in ['CalFresh', 'CalWORKs', 'Medi-Cal']:
    pdocs = [d for d in docs if prog in d.get('programs', [])]
    removed_ids = set()
    
    for i in range(len(pdocs)):
        if pdocs[i]['id'] in removed_ids: continue
        for j in range(i + 1, len(pdocs)):
            if pdocs[j]['id'] in removed_ids: continue
            
            d1, d2 = pdocs[i], pdocs[j]
            t1, t2 = d1['title'], d2['title']
            n1, n2 = normalize_title(t1), normalize_title(t2)
            c1, c2 = d1.get('content', '').strip(), d2.get('content', '').strip()
            sec1, sec2 = extract_section_code(t1), extract_section_code(t2)
            
            is_dupe = False
            reason = ''
            
            # Case 1: Identical normalized title
            if n1 == n2:
                is_dupe = True
                reason = f"identical normalized title ({n1})"
            # Case 2: One is bare section code of the other
            elif sec1 and sec2 and sec1 == sec2:
                bare1 = re.sub(r'[^a-z0-9]', '', t1.lower()) == sec1
                bare2 = re.sub(r'[^a-z0-9]', '', t2.lower()) == sec2
                if bare1 or bare2:
                    is_dupe = True
                    reason = f"bare section code vs full title"
                elif c1 and c2 and c1 == c2:
                    is_dupe = True
                    reason = f"same section code and identical content"
                elif 'cfet' in t1.lower() and 'cfet' in t2.lower():
                    is_dupe = True
                    reason = f"CFET duplicate"
            # Case 3: Identical EITC duplicate
            elif len(c1) > 100 and c1 == c2 and ('earned income tax credit' in t1.lower() and 'earned income tax credit' in t2.lower()):
                is_dupe = True
                reason = f"identical EITC content"
                
            if is_dupe:
                # Score to keep the cleaner/richer title
                s1 = (10 if '_' not in t1 else 0) + len(t1)
                s2 = (10 if '_' not in t2 else 0) + len(t2)
                
                kept, to_remove = (d1, d2) if s1 >= s2 else (d2, d1)
                removed_ids.add(to_remove['id'])
                print(f"[{prog}] Removed duplicate: '{to_remove['title']}' ({to_remove['id']}) in favor of '{kept['title']}' ({kept['id']}) [Reason: {reason}]")

    prog_clean = [d for d in pdocs if d['id'] not in removed_ids]
    clean_docs.extend(prog_clean)
    print(f"[{prog}] Before: {len(pdocs)}, After: {len(prog_clean)} (Removed {len(removed_ids)})")

# Save cleaned catalog
with open(DOCS_PATH, 'w', encoding='utf-8') as f:
    json.dump(clean_docs, f, indent=2)

print(f"Cleaned documents.json saved! Total unique documents: {len(clean_docs)}")
