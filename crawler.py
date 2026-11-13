"""Discovery crawler for the County portal.

Writes raw search hits to data/crawl/documents.raw.json for review. It never
touches data/documents.json (the curated catalog the app serves) and does not
create PDFs: merge reviewed entries into the catalog by hand.
"""

import os
import json
import time
import urllib.request
import http.cookiejar
from typing import Dict, List, Any

BASE_URL = "https://file.sandiegocounty.gov/HHSAPublicSite"
MODULE_VERSION = "zxF+S8oCjmRatPW60zkGuw"
CSRF_TOKEN = "T6C+9iB49TLra4jEsMeSckDMNhQ="

PROGRAMS = {
    "CalFresh": 542,
    "CalWORKs": 448,
    "Medi-Cal": 599
}

class SDBenefitsCrawler:
    def __init__(self, output_dir: str = os.path.join("data", "crawl")):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        self._init_session()

    def _init_session(self):
        """Initializes OutSystems anonymous session and obtains session cookies."""
        req = urllib.request.Request(
            f"{BASE_URL}/moduleservices/roles",
            headers={
                "Accept": "application/json",
                "OutSystems-Client-Env": "browser",
                "X-CSRFToken": CSRF_TOKEN
            }
        )
        try:
            with self.opener.open(req) as resp:
                print(f"[*] Session initialized with status {resp.status}")
        except Exception as e:
            print(f"[!] Warning during session initialization: {e}")

    def search_documents(self, query: str = "", start_index: int = 0, max_records: int = 50) -> Dict[str, Any]:
        """Queries the County OpenSearch backend via OutSystems DataActionSearchPublic."""
        payload = {
            "versionInfo": {
                "moduleVersion": MODULE_VERSION,
                "apiVersion": "JxHJhGsp1SU84IE57myVbQ"
            },
            "viewName": "MainFlow.Section",
            "screenData": {
                "variables": {
                    "folderIdIn": "0",
                    "searchTextVar": query,
                    "searchedTextVar": query,
                    "startIndexVar": start_index,
                    "maxRecordsVar": max_records
                }
            }
        }
        api_url = f"{BASE_URL}/screenservices/HHSAPublicSite/MainFlow/Section/DataActionSearchPublic"
        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "Accept": "application/json",
                "OutSystems-Client-Env": "browser",
                "X-CSRFToken": CSRF_TOKEN
            }
        )
        with self.opener.open(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def crawl_all_documents(self, queries: List[str] = None):
        """
        Crawls and aggregates all policy documents across CalFresh, CalWORKs, and Medi-Cal.
        Saves all unique documents with full extracted text, titles, dates, and official URLs.
        """
        if queries is None:
            # High-coverage keywords to pull all policy sections
            queries = [
                "eligibility", "income", "deduction", "reporting", "household", 
                "student", "citizenship", "verification", "sanction", "allotment", 
                "emergency", "expedited", "SAR 7", "calfresh", "calworks", "medi-cal",
                "property", "assets", "allowance", "disability", "work"
            ]

        all_docs: Dict[str, Dict[str, Any]] = {}
        print(f"[*] Starting document discovery using {len(queries)} seed queries...")

        for query in queries:
            start_index = 0
            page_size = 50
            print(f"[*] Querying seed: '{query}'...")
            
            while True:
                try:
                    res = self.search_documents(query, start_index=start_index, max_records=page_size)
                    files_found = res.get("data", {}).get("FilesFound", {})
                    hits = files_found.get("Hits", {}).get("Hits", {}).get("List", [])
                    total = int(files_found.get("Hits", {}).get("Total", {}).get("Value", 0))

                    if not hits:
                        break

                    for h in hits:
                        s = h.get("source", {})
                        doc_id = str(s.get("Id", "")).strip()
                        if not doc_id:
                            continue

                        if doc_id not in all_docs:
                            title = s.get("Title", "").strip()
                            content = s.get("FileContentText", "").strip()
                            published_on = s.get("PublishedOn", "")
                            file_type = s.get("FileType", "PDF")
                            
                            # Determine likely program tags based on title and content
                            lower_text = (title + " " + content[:2000]).lower()
                            programs = []
                            if "calfresh" in lower_text or "food stamps" in lower_text or "snap" in lower_text or "63-" in title:
                                programs.append("CalFresh")
                            if "calworks" in lower_text or "cash aid" in lower_text or "tanf" in lower_text or "42-" in title or "40-" in title:
                                programs.append("CalWORKs")
                            if "medi-cal" in lower_text or "medical" in lower_text or "magi" in lower_text or "cms" in lower_text:
                                programs.append("Medi-Cal")
                            if not programs:
                                programs = ["General / Multiple"]

                            all_docs[doc_id] = {
                                "id": doc_id,
                                "title": title,
                                "programs": programs,
                                "published_on": published_on,
                                "file_type": file_type,
                                "local_pdf_url": "",
                                "official_url": f"{BASE_URL}/View?FileId={doc_id}",
                                "content": content
                            }

                    start_index += len(hits)
                    if start_index >= min(total, 300):  # Cap per seed query to avoid rate limits
                        break
                    time.sleep(0.3)
                except Exception as e:
                    print(f"[!] Error querying '{query}' at index {start_index}: {e}")
                    break

        print(f"\n[✓] Crawling complete! Total unique policy documents collected: {len(all_docs)}")
        
        # Save aggregated documents
        out_path = os.path.join(self.output_dir, "documents.raw.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(list(all_docs.values()), f, indent=2, ensure_ascii=False)
        print(f"[✓] Saved to {out_path} (data/documents.json was not modified)")

if __name__ == "__main__":
    crawler = SDBenefitsCrawler()
    crawler.crawl_all_documents()
