import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ai_backend import answer_question
from search_engine import get_engine

app = FastAPI(title="San Diego County Benefits Policy Search & AI Assistant")

PDF_DIR = os.path.join(os.path.dirname(__file__), "data", "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)
app.mount("/pdfs", StaticFiles(directory=PDF_DIR), name="pdfs")

# Public read-only API: any origin may call it, but no cookies or credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

ENGINE = get_engine()
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
