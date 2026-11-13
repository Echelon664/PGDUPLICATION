"""Compare the stored PDFs against the County of San Diego HHSA public site.

The County portal (https://file.sandiegocounty.gov/HHSAPublicSite/) lists every
published file per folder and serves the file bytes to its own PDF viewer. This
module reads the same public listing and compares each County file with the
copy stored in data/pdfs/.

Two scan modes:

    quick   Listing only (about a minute). Compares County file IDs and publish
            dates with the manifest saved by the last full scan.
    full    Also downloads every County file and compares its SHA-256 with the
            stored PDF (10-20 minutes, ~450 downloads).

The scan is report-only: it never changes data/documents.json or data/pdfs/.

CLI:
    python3 county_sync.py quick
    python3 county_sync.py full

Results are written to data/county_sync/report.json (latest report) and
data/county_sync/manifest.json (what the last full scan verified).
"""

import base64
import hashlib
import hmac
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_PATH = os.path.join(BASE_DIR, "data", "documents.json")
PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")
SYNC_DIR = os.path.join(BASE_DIR, "data", "county_sync")
REPORT_PATH = os.path.join(SYNC_DIR, "report.json")
MANIFEST_PATH = os.path.join(SYNC_DIR, "manifest.json")

COUNTY_BASE = "https://file.sandiegocounty.gov/HHSAPublicSite"
PROGRAM_ROOTS = {"CalFresh": 542, "CalWORKs": 448, "Medi-Cal": 599}

# The portal's token for anonymous visitors (the same value every browser sends).
ANONYMOUS_CSRF = "T6C+9iB49TLra4jEsMeSckDMNhQ="
USER_AGENT = "Mozilla/5.0 (compatible; program-guide-sync)"

# Pause between County requests so a scan stays gentle on their server.
REQUEST_DELAY = float(os.environ.get("COUNTY_SYNC_DELAY", "0.15"))

SVC_CHILD_FOLDERS = "screenservices/HHSAPublicSite/MainFlow/Section_SecondLevel/ScreenDataSetGetById_Folder"
SVC_FOLDER_FILES = "screenservices/HHSAPublicSite/MainFlow/Section_SecondLevelFiles/ScreenDataSetGetByFolderId_Files"
SVC_FILE_RECORD = "screenservices/HHSAPublicSite/MainFlow/View/ScreenDataSetGetFileRecordById"
SVC_BUCKET = "screenservices/HHSAPublicSite/MainFlow/View/DataActionGetAWSBucketId"
SVC_GET_FILE = "screenservices/CoreFileManagementCore_CW/FileBlocks/FilePreview_WB_Aspose_withEmail/DataActionGetFile"

# Scripts that declare the API version of each service above.
_SCRIPT_HINTS = (
    "MainFlow.Section_SecondLevel.mvc.js",
    "MainFlow.Section_SecondLevelFiles.mvc.js",
    "MainFlow.View.mvc.js",
    "FilePreview_WB_Aspose_withEmail.mvc.js",
)

# The County re-stamps the PDF trailer /ID on each download of some files, so
# two downloads of the same document differ in those bytes only.
_PDF_ID_RE = re.compile(rb"/ID\s*\[\s*<[0-9A-Fa-f]*>\s*<[0-9A-Fa-f]*>\s*\]")


class CountyError(RuntimeError):
    pass


def content_hash(data: bytes) -> str:
    """SHA-256 of a PDF with the volatile trailer /ID blanked out."""
    return hashlib.sha256(_PDF_ID_RE.sub(b"/ID[<><>]", data)).hexdigest()


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower().replace("_", " ")).strip()


# ------------------------------------------------------------------- County
class CountyClient:
    def __init__(self, delay: float = REQUEST_DELAY, timeout: float = 90.0):
        self.delay = delay
        self.timeout = timeout
        self.module_version = ""
        self.api_versions: Dict[str, str] = {}
        self._bucket_id: Optional[str] = None

    def _open(self, req: urllib.request.Request) -> bytes:
        last: Optional[Exception] = None
        for attempt in range(3):
            if self.delay:
                time.sleep(self.delay)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return resp.read()
            except urllib.error.HTTPError as exc:
                if exc.code < 500 and exc.code != 429:
                    raise CountyError(f"County site returned HTTP {exc.code} for {req.full_url}")
                last = exc
            except (urllib.error.URLError, OSError) as exc:
                last = exc
            time.sleep(1.5 * (attempt + 1))
        raise CountyError(f"County site unreachable: {last}")

    def _get_text(self, path: str) -> str:
        req = urllib.request.Request(COUNTY_BASE + path, headers={"User-Agent": USER_AGENT})
        return self._open(req).decode("utf-8", "replace")

    def discover(self) -> None:
        """Read the portal's current version tokens (they change on each County deploy)."""
        self.module_version = json.loads(self._get_text("/moduleservices/moduleversioninfo"))["versionToken"]
        manifest = json.loads(self._get_text("/moduleservices/moduleinfo"))["manifest"]["urlVersions"]
        versions: Dict[str, str] = {}
        for hint in _SCRIPT_HINTS:
            key = next((u for u in manifest if hint in u), None)
            if not key:
                raise CountyError(f"County site layout changed: {hint} not found")
            path = key[len("/HHSAPublicSite"):] if key.startswith("/HHSAPublicSite") else key
            script = self._get_text(path + manifest[key])
            for match in re.finditer(r'"(screenservices/[^"]+)",\s*"([^"]+)"', script):
                versions[match.group(1)] = match.group(2)
        missing = [s for s in (SVC_CHILD_FOLDERS, SVC_FOLDER_FILES, SVC_FILE_RECORD, SVC_BUCKET, SVC_GET_FILE)
                   if s not in versions]
        if missing:
            raise CountyError("County site layout changed: missing " + ", ".join(m.rsplit("/", 1)[-1] for m in missing))
        self.api_versions = versions

    def _call(self, service: str, view: str, variables: Dict[str, Any],
              input_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.api_versions:
            self.discover()
        body: Dict[str, Any] = {
            "versionInfo": {"moduleVersion": self.module_version, "apiVersion": self.api_versions[service]},
            "viewName": view,
            "screenData": {"variables": variables},
        }
        if input_parameters is not None:
            body["inputParameters"] = input_parameters
        req = urllib.request.Request(
            COUNTY_BASE + "/" + service,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "Accept": "application/json",
                "X-CSRFToken": ANONYMOUS_CSRF,
                "User-Agent": USER_AGENT,
            },
        )
        payload = json.loads(self._open(req).decode("utf-8"))
        if "data" not in payload:
            raise CountyError(f"Unexpected County response from {service.rsplit('/', 1)[-1]}")
        return payload["data"]

    _ALL = {"StartIndex": 0, "MaxRecords": 2147483647}

    def child_folders(self, folder_id: str) -> List[Tuple[str, str]]:
        data = self._call(SVC_CHILD_FOLDERS, "MainFlow.Section",
                          {"FolderId": str(folder_id), "IsExpanded": True}, self._ALL)
        return [(row["Folder"]["Id"], (row["Folder"].get("Name") or "").strip())
                for row in data["List"]["List"] if row["Folder"]["Id"] != str(folder_id)]

    def folder_files(self, folder_id: str) -> List[Dict[str, str]]:
        data = self._call(SVC_FOLDER_FILES, "MainFlow.Section",
                          {"FolderId": str(folder_id), "TableSort": "{File}.[Name] ASC"}, self._ALL)
        return [{
            "file_id": row["FileRecord"]["Id"],
            "title": (row["File"].get("Title") or "").strip(),
            "published_on": row["File"].get("PublishedOn") or "",
        } for row in data["List"]["List"] if row["FileRecord"]["Id"] not in ("", "0")]

    def list_program(self, program: str) -> List[Dict[str, Any]]:
        files: List[Dict[str, Any]] = []
        seen_folders = set()

        def walk(folder_id: str, path: List[str], depth: int) -> None:
            if folder_id in seen_folders or depth > 8:
                return
            seen_folders.add(folder_id)
            for entry in self.folder_files(folder_id):
                files.append({**entry, "program": program, "path": path})
            for child_id, name in self.child_folders(folder_id):
                walk(child_id, path + [name], depth + 1)

        walk(str(PROGRAM_ROOTS[program]), [], 0)
        return files

    def fetch_file(self, file_id: str) -> bytes:
        variables = {"FileId": str(file_id), "_fileIdInDataFetchStatus": 1}
        record = self._call(SVC_FILE_RECORD, "MainFlow.View", variables, {})
        rows = record["List"]["List"]
        s3_id = rows[0]["FileRecord"]["S3FileId"] if rows else "0"
        if s3_id in ("", "0"):
            raise CountyError(f"County file {file_id} has no stored content")
        if self._bucket_id is None:
            self._bucket_id = self._call(SVC_BUCKET, "MainFlow.View", variables)["AWSBucketId"]
        data = self._call(SVC_GET_FILE, "MainFlow.View", {
            "AWSBucketId": self._bucket_id, "_aWSBucketIdInDataFetchStatus": 1,
            "S3FileId": s3_id, "_s3FileIdInDataFetchStatus": 1,
            "ShowPrintButton": True, "_showPrintButtonInDataFetchStatus": 1,
            "ShowDownloadButton": False, "_showDownloadButtonInDataFetchStatus": 1,
            "Is100VHVW": True, "_is100VHVWInDataFetchStatus": 1,
            "SlidesConfig_AllColumnsInOnePagePerSheet": False,
            "_slidesConfig_AllColumnsInOnePagePerSheetInDataFetchStatus": 1,
            "WindowWidth": "768px", "WindowHeight": "576px",
            "EventList": {"List": [], "EmptyListItem": ""},
        })
        encoded = (data.get("File") or {}).get("BinaryData") or ""
        if not encoded:
            raise CountyError(f"County file {file_id} came back empty")
        return base64.b64decode(encoded)


def county_view_url(file_id: str) -> str:
    return f"{COUNTY_BASE}/View?FileId={urllib.parse.quote(str(file_id))}"


# -------------------------------------------------------------------- local
def load_local_docs(docs_path: str = DOCS_PATH, pdf_dir: str = PDF_DIR) -> List[Dict[str, Any]]:
    """Catalog entries with the hash of their stored PDF (None when there is no file)."""
    with open(docs_path, "r", encoding="utf-8") as f:
        docs = json.load(f)
    cache: Dict[str, Optional[Tuple[str, int]]] = {}
    out = []
    for doc in docs:
        url = doc.get("local_pdf_url") or ""
        filename = urllib.parse.unquote(os.path.basename(url)) if url else ""
        info: Optional[Tuple[str, int]] = None
        if filename:
            if filename not in cache:
                path = os.path.join(pdf_dir, filename)
                if os.path.isfile(path):
                    with open(path, "rb") as f:
                        data = f.read()
                    cache[filename] = (content_hash(data), len(data))
                else:
                    cache[filename] = None
            info = cache[filename]
        programs = doc.get("programs") or []
        out.append({
            "id": doc.get("id"),
            "title": doc.get("title", ""),
            "program": programs[0] if programs else "",
            "chapter": doc.get("chapter", ""),
            "filename": filename,
            "hash": info[0] if info else None,
            "size": info[1] if info else None,
            "source_missing": bool(doc.get("source_missing")),
        })
    return out


# ------------------------------------------------------------------ compare
def hash_stored_files(pdf_dir: str = PDF_DIR) -> Dict[str, str]:
    """Content hash -> file name for every PDF on disk, including ones no catalog entry uses."""
    out: Dict[str, str] = {}
    for name in sorted(os.listdir(pdf_dir)):
        path = os.path.join(pdf_dir, name)
        if name.lower().endswith(".pdf") and os.path.isfile(path):
            with open(path, "rb") as f:
                out.setdefault(content_hash(f.read()), name)
    return out


def compare(county_files: List[Dict[str, Any]], local_docs: List[Dict[str, Any]],
            mode: str, stored_files: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Classify every County file and every stored document.

    county_files entries carry `hash` (full mode: SHA-256 of the County bytes),
    or `verified` (quick mode: manifest entry from the last full scan, if the
    file ID and publish date are unchanged), or `error`.
    """
    by_hash: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    by_title: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    by_id = {d["id"]: d for d in local_docs}
    for doc in local_docs:
        if doc["hash"]:
            by_hash.setdefault((doc["program"], doc["hash"]), []).append(doc)
        by_title.setdefault((doc["program"], normalize_title(doc["title"])), []).append(doc)

    groups: Dict[str, List[Dict[str, Any]]] = {
        "identical": [], "changed": [], "mislabelled": [], "missing": [],
        "unverified": [], "errors": [], "not_on_county": [],
    }
    matched_docs = set()

    def row(cf: Dict[str, Any], doc: Optional[Dict[str, Any]], note: str = "") -> Dict[str, Any]:
        return {
            "program": cf["program"],
            "county_file_id": cf["file_id"],
            "county_title": cf["title"],
            "county_path": " / ".join(cf.get("path") or []),
            "county_published_on": cf.get("published_on", ""),
            "county_url": county_view_url(cf["file_id"]),
            "doc_id": doc["id"] if doc else None,
            "doc_title": doc["title"] if doc else None,
            "stored_file": doc["filename"] if doc else None,
            "note": note,
        }

    for cf in county_files:
        title_docs = by_title.get((cf["program"], normalize_title(cf["title"])), [])
        title_doc = title_docs[0] if len(title_docs) == 1 else None

        if cf.get("error"):
            groups["errors"].append(row(cf, title_doc, cf["error"]))
            if title_doc:
                matched_docs.add(title_doc["id"])
            continue

        if mode == "quick":
            verified = cf.get("verified")
            doc = by_id.get(verified.get("doc_id")) if verified else None
            if verified and doc and doc["hash"] == verified.get("hash"):
                groups["identical"].append(row(cf, doc, "Unchanged since the last full scan"))
                matched_docs.add(doc["id"])
            elif title_doc and (title_doc["source_missing"] or not title_doc["hash"]):
                groups["missing"].append(row(cf, title_doc, "Listed in the catalog without a stored PDF"))
                matched_docs.add(title_doc["id"])
            elif title_doc or doc:
                target = title_doc or doc
                prev = cf.get("previous")
                if not prev:
                    reason = "New on the County site since the last full scan, or never checked"
                elif prev.get("published_on") != cf["published_on"]:
                    reason = "Republished by the County since the last full scan"
                elif not prev.get("doc_id"):
                    groups["changed"].append(row(cf, target, "Differed at the last full scan"))
                    matched_docs.add(target["id"])
                    continue
                else:
                    reason = "Stored PDF changed since the last full scan"
                groups["unverified"].append(row(cf, target, reason))
                matched_docs.add(target["id"])
            else:
                groups["missing"].append(row(cf, None, "No catalog entry with this title"))
            continue

        hash_docs = by_hash.get((cf["program"], cf["hash"]), [])
        if hash_docs:
            # Prefer the entry whose title also matches.
            doc = next((d for d in hash_docs if title_doc and d["id"] == title_doc["id"]), hash_docs[0])
            matched_docs.add(doc["id"])
            if title_doc and title_doc["id"] != doc["id"]:
                # Same bytes stored under another entry; the entry with this title holds something else.
                matched_docs.add(title_doc["id"])
                groups["mislabelled"].append(row(
                    cf, title_doc,
                    f"The County's file for this title is stored under \"{doc['title']}\" ({doc['id']}) instead"))
            elif not title_doc and normalize_title(doc["title"]) != normalize_title(cf["title"]):
                groups["identical"].append(row(cf, doc, "Same file; the catalog title differs from the County title"))
            else:
                groups["identical"].append(row(cf, doc))
        elif title_doc:
            matched_docs.add(title_doc["id"])
            if title_doc["source_missing"] or not title_doc["hash"]:
                groups["missing"].append(row(cf, title_doc, "Listed in the catalog without a stored PDF"))
            else:
                groups["changed"].append(row(cf, title_doc, "Stored PDF differs from the County's current file"))
        else:
            on_disk = (stored_files or {}).get(cf["hash"])
            groups["missing"].append(row(
                cf, None,
                f"No catalog entry; the file is already on disk as \"{on_disk}\"" if on_disk
                else "No catalog entry with this title"))

    for doc in local_docs:
        if doc["id"] in matched_docs:
            continue
        groups["not_on_county"].append({
            "program": doc["program"], "doc_id": doc["id"], "doc_title": doc["title"],
            "stored_file": doc["filename"] or None,
            "note": "No County file has this title or these contents"
                    + ("" if doc["hash"] else " (and no PDF is stored)"),
        })

    summary = {name: len(rows) for name, rows in groups.items()}
    summary["county_files"] = len(county_files)
    summary["stored_documents"] = len(local_docs)
    in_sync = (mode == "full" and len(county_files) > 0
               and all(summary[k] == 0 for k in ("changed", "mislabelled", "missing", "errors", "not_on_county")))
    return {"summary": summary, "in_sync": in_sync, "groups": groups}


# --------------------------------------------------------------------- scan
def _read_json(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    os.replace(tmp, path)


def run_scan(mode: str = "quick",
             progress: Optional[Callable[[str, int, int], None]] = None,
             client: Optional[CountyClient] = None) -> Dict[str, Any]:
    if mode not in ("quick", "full"):
        raise ValueError("mode must be 'quick' or 'full'")
    progress = progress or (lambda stage, done, total: None)
    client = client or CountyClient()
    started = time.time()

    county_files: List[Dict[str, Any]] = []
    for i, program in enumerate(PROGRAM_ROOTS):
        progress(f"Listing {program} on the County site", i, len(PROGRAM_ROOTS))
        county_files.extend(client.list_program(program))
    if not county_files:
        raise CountyError("The County site listed no files; nothing was compared")

    progress("Hashing stored PDFs", 0, 1)
    local_docs = load_local_docs()
    manifest = (_read_json(MANIFEST_PATH) or {}).get("files", {})

    if mode == "full":
        for i, cf in enumerate(county_files):
            progress(f"Downloading County files ({cf['program']})", i, len(county_files))
            try:
                data = client.fetch_file(cf["file_id"])
                cf["hash"] = content_hash(data)
                cf["size"] = len(data)
            except CountyError as exc:
                cf["error"] = str(exc)
    else:
        for cf in county_files:
            prev = manifest.get(cf["file_id"])
            if prev:
                cf["previous"] = prev
                if prev.get("published_on") == cf["published_on"] and prev.get("doc_id"):
                    cf["verified"] = prev

    result = compare(county_files, local_docs, mode, hash_stored_files() if mode == "full" else None)
    report = {
        "mode": mode,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "duration_seconds": round(time.time() - started, 1),
        "source": COUNTY_BASE + "/",
        **result,
    }

    if mode == "full":
        doc_for = {r["county_file_id"]: r["doc_id"] for r in result["groups"]["identical"]}
        _write_json(MANIFEST_PATH, {
            "verified_at": report["finished_at"],
            "files": {
                cf["file_id"]: {
                    "title": cf["title"], "program": cf["program"], "path": cf.get("path") or [],
                    "published_on": cf["published_on"],
                    "hash": cf.get("hash"), "size": cf.get("size"),
                    "doc_id": doc_for.get(cf["file_id"]),
                } for cf in county_files if not cf.get("error")
            },
        })
    else:
        last_full = _read_json(MANIFEST_PATH) or {}
        report["last_full_scan"] = last_full.get("verified_at")
    _write_json(REPORT_PATH, report)
    progress("Done", 1, 1)
    return report


# ------------------------------------------------- web: background + status
_STATE_LOCK = threading.Lock()
_STATE: Dict[str, Any] = {"running": False, "mode": None, "stage": "", "done": 0, "total": 0,
                          "started_at": None, "error": None}


def admin_enabled() -> bool:
    return bool(os.environ.get("ADMIN_TOKEN", "").strip())


def check_admin(token: Optional[str]) -> bool:
    expected = os.environ.get("ADMIN_TOKEN", "").strip()
    if not expected or not token:
        return False
    return hmac.compare_digest(token.strip().encode("utf-8"), expected.encode("utf-8"))


def status() -> Dict[str, Any]:
    with _STATE_LOCK:
        state = dict(_STATE)
    report = _read_json(REPORT_PATH)
    state["admin_enabled"] = admin_enabled()
    state["last_report"] = {
        k: report.get(k) for k in ("mode", "finished_at", "duration_seconds", "summary", "in_sync", "last_full_scan")
    } if report else None
    return state


def load_report() -> Optional[Dict[str, Any]]:
    return _read_json(REPORT_PATH)


def start_scan(mode: str) -> bool:
    """Start a scan in the background. Returns False if one is already running."""
    if mode not in ("quick", "full"):
        raise ValueError("mode must be 'quick' or 'full'")
    with _STATE_LOCK:
        if _STATE["running"]:
            return False
        _STATE.update(running=True, mode=mode, stage="Starting", done=0, total=0,
                      started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), error=None)

    def progress(stage: str, done: int, total: int) -> None:
        with _STATE_LOCK:
            _STATE.update(stage=stage, done=done, total=total)

    def worker() -> None:
        error = None
        try:
            run_scan(mode, progress)
        except Exception as exc:  # report the failure instead of killing the thread silently
            error = str(exc) or exc.__class__.__name__
            print(f"[sync] scan failed: {error}")
        with _STATE_LOCK:
            _STATE.update(running=False, error=error)

    threading.Thread(target=worker, name="county-sync", daemon=True).start()
    return True


if __name__ == "__main__":
    scan_mode = sys.argv[1] if len(sys.argv) > 1 else "quick"
    last = {"stage": ""}

    def show(stage: str, done: int, total: int) -> None:
        if stage != last["stage"] or (total and done % 25 == 0):
            print(f"  {stage} {done}/{total}" if total > 1 else f"  {stage}", flush=True)
            last["stage"] = stage

    try:
        final = run_scan(scan_mode, show)
    except (CountyError, ValueError) as exc:
        sys.exit(f"Scan failed: {exc}")
    print(json.dumps(final["summary"], indent=1))
    print("In sync with the County site." if final["in_sync"] else f"Report: {REPORT_PATH}")
