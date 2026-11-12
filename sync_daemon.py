#!/usr/bin/env python3
import os, glob, json, time, re, shutil, urllib.parse, zlib

DATA_DIR = "/Users/echelon619/Desktop/ChrisPG/data"
PDF_DIR = os.path.join(DATA_DIR, "pdfs")
DL_DIR = "/Users/echelon619/.gemini/antigravity/brain/df70e671-e6fb-4e6d-b828-18340155569b/browser_sandbox/downloads"
DOCS_FILE = os.path.join(DATA_DIR, "documents.json")
CW_CATALOG_FILE = os.path.join(DATA_DIR, "calworks_catalog.json")
MC_CATALOG_FILE = os.path.join(DATA_DIR, "medical_catalog.json")

def normalize(name):
    return re.sub(r'[^a-z0-9]', '', name.lower())

def extract_pdf_bt_text(filepath):
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
    except Exception:
        return ''
    out = []
    pos = 0
    while True:
        s = data.find(b'stream', pos)
        if s == -1: break
        s_start = data.find(b'\n', s)
        if s_start == -1: break
        s_start += 1
        e = data.find(b'endstream', s_start)
        if e == -1: break
        raw = data[s_start:e].strip()
        pos = e + 9
        if not raw: continue
        try:
            decomp = zlib.decompress(raw)
        except Exception:
            continue
        
        bt_pos = 0
        while True:
            bt_idx = decomp.find(b'BT', bt_pos)
            if bt_idx == -1: break
            et_idx = decomp.find(b'ET', bt_idx)
            if et_idx == -1: et_idx = len(decomp)
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
                            if paren > 0: buf.append(b')')
                            j += 1
                        else:
                            buf.append(c)
                            j += 1
                    txt = b''.join(buf).decode('latin1', 'ignore').strip()
                    if txt: out.append(txt)
                    i = j
                else:
                    i += 1
            bt_pos = et_idx + 2
    return re.sub(r'\s+', ' ', ' '.join(out)).strip()

def run_sync():
    step_files = sorted(glob.glob('/Users/echelon619/.gemini/antigravity/brain/**/step_*.json', recursive=True))
    mapping = {}
    for sf in step_files:
        try:
            with open(sf) as f:
                d = json.load(f)
                val = d.get('value', {})
                dc = d.get('downloads_completed', [])
                if isinstance(val, dict):
                    br = val.get('batchResults') or val.get('results')
                    if isinstance(br, list):
                        for i, item in enumerate(br):
                            fn = item.get('filename') or (item.get('savePath').split('/')[-1] if item.get('savePath') else None)
                            title = item.get('title')
                            if fn and title and fn != 'unknown':
                                mapping[fn] = title.strip()
                            elif dc and i < len(dc) and title:
                                dc_fn = dc[i].get('savePath', '').split('/')[-1]
                                if dc_fn: mapping[dc_fn] = title.strip()
        except Exception:
            pass

    # Copy files
    copied = 0
    for fn, title in mapping.items():
        src = os.path.join(DL_DIR, fn)
        safe_title = title.replace('/', '_').replace(':', ' -') + '.pdf'
        dst = os.path.join(PDF_DIR, safe_title)
        if os.path.exists(src):
            if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src):
                shutil.copy2(src, dst)
                copied += 1

    available_pdfs = sorted(os.listdir(PDF_DIR))

    def find_pdf_for_title(title):
        norm_title = normalize(title)
        for fn in available_pdfs:
            norm_fn = normalize(fn.replace('.pdf', ''))
            if norm_fn == norm_title: return fn
        for fn in available_pdfs:
            norm_fn = normalize(fn.replace('.pdf', ''))
            if norm_fn.startswith(norm_title[:15]) or norm_title.startswith(norm_fn[:15]): return fn
        prefix = title.split()[0] if title.split() else ''
        if len(prefix) > 3:
            for fn in available_pdfs:
                if fn.startswith(prefix): return fn
        return None

    # Load existing docs
    try:
        with open(DOCS_FILE) as f:
            docs = json.load(f)
    except Exception:
        return

    updated = False
    for doc in docs:
        if not doc.get('local_pdf_url', '').startswith('/pdfs/'):
            matched = find_pdf_for_title(doc['title'])
            if matched:
                doc['local_pdf_url'] = f"/pdfs/{urllib.parse.quote(matched)}"
                text = extract_pdf_bt_text(os.path.join(PDF_DIR, matched))
                if text:
                    doc['content'] = text[:12000]
                    if doc.get('sections'):
                        doc['sections'][0]['text'] = text[:4000]
                updated = True

    if updated or copied > 0:
        with open(DOCS_FILE, 'w') as f:
            json.dump(docs, f, indent=2)
        print(f"[*] Sync complete. Copied: {copied}, Total PDFs in pdf_dir: {len(available_pdfs)}")

if __name__ == '__main__':
    while True:
        try:
            run_sync()
        except Exception as e:
            print(f"[!] Sync error: {e}")
        time.sleep(15)
