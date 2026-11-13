import mimetypes
import os
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import catalog
import county_sync
from ai_backend import answer_question
from search_engine import get_engine

app = FastAPI(title="San Diego County Benefits Policy Search & AI Assistant")

PDF_DIR = os.path.join(os.path.dirname(__file__), "data", "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)
app.mount("/pdfs", StaticFiles(directory=PDF_DIR), name="pdfs")

# PDF.js viewer (static/pdfjs). Its modules, locales and decoders need correct MIME types.
for _ext, _type in ((".mjs", "text/javascript"), (".ftl", "text/plain"), (".wasm", "application/wasm"),
                    (".bcmap", "application/octet-stream"), (".pfb", "application/octet-stream"),
                    (".icc", "application/octet-stream")):
    mimetypes.add_type(_type, _ext)
PDFJS_DIR = os.path.join(os.path.dirname(__file__), "static", "pdfjs")
if os.path.isdir(PDFJS_DIR):
    app.mount("/pdfjs", StaticFiles(directory=PDFJS_DIR), name="pdfjs")

# Public read-only API: any origin may call it, but no cookies or credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

ENGINE = get_engine()
catalog.ensure_page()
print(f"[✓] Search engine ready: {ENGINE.stats()}")


class AskRequest(BaseModel):
    question: str
    program: Optional[str] = "All"


@app.get("/api/search")
def search_documents(
    q: Optional[str] = Query("", max_length=300),
    program: str = "All",
    limit: int = Query(50, ge=1, le=250),
):
    results = ENGINE.search(q or "", program_filter=program, top_k=limit)
    return {
        "query": q,
        "program": program,
        "total": len(results),
        "results": results,
    }


@app.post("/api/ask")
def ask_question(req: AskRequest, request: Request):
    client_id = request.client.host if request.client else "unknown"
    try:
        return answer_question(ENGINE, req.question, req.program or "All", client_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


class ScanRequest(BaseModel):
    mode: str = "quick"


@app.get("/api/sync/status")
def sync_status():
    return county_sync.status()


@app.get("/api/sync/report")
def sync_report():
    report = county_sync.load_report()
    if report is None:
        raise HTTPException(status_code=404, detail="No scan has been run yet")
    return report


@app.post("/api/sync/scan")
def sync_scan(req: ScanRequest, x_admin_token: Optional[str] = Header(None)):
    # A scan downloads hundreds of files from the County, so it is admin-only.
    if not county_sync.admin_enabled():
        raise HTTPException(status_code=503, detail="Scans are disabled: set ADMIN_TOKEN on the server")
    if not county_sync.check_admin(x_admin_token):
        raise HTTPException(status_code=403, detail="Invalid admin token")
    if req.mode not in ("quick", "full"):
        raise HTTPException(status_code=400, detail="mode must be 'quick' or 'full'")
    if not county_sync.start_scan(req.mode):
        raise HTTPException(status_code=409, detail="A scan is already running")
    return {"started": True, "mode": req.mode}


@app.get("/sync", response_class=HTMLResponse)
def sync_page():
    with open(os.path.join(os.path.dirname(__file__), "templates", "sync.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/health")
def health():
    stats = ENGINE.stats()
    return {
        "status": "ok",
        "engine": stats.get("engine"),
        "docs": stats.get("docs"),
        "chunks": stats.get("chunks"),
    }


@app.get("/", response_class=HTMLResponse)
def index_page():
    html_file = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>San Diego County Benefits Search API is running.</h1>"
