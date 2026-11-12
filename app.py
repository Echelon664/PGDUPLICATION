import os
import json
import urllib.request
from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi.staticfiles import StaticFiles

from indexer import BM25Index, chunk_documents

app = FastAPI(title="San Diego County Benefits Policy Search & AI Assistant")

PDF_DIR = os.path.join(os.path.dirname(__file__), "data", "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)
app.mount("/pdfs", StaticFiles(directory=PDF_DIR), name="pdfs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOCS_FILE = os.path.join(os.path.dirname(__file__), "data", "documents.json")
INDEX = BM25Index()
CHUNKS = []

def initialize_index():
    global CHUNKS, INDEX
    if os.path.exists(DOCS_FILE):
        CHUNKS = chunk_documents(DOCS_FILE)
        INDEX.build(CHUNKS)
        print(f"[✓] Search index initialized with {len(CHUNKS)} policy chunks.")
    else:
        print("[!] Warning: data/documents.json not found. Run crawler.py first.")

initialize_index()

class AskRequest(BaseModel):
    question: str
    program: Optional[str] = "All"
    model_provider: Optional[str] = "auto" # 'ollama', 'gemini', 'mock'

def call_ollama(prompt: str, model: str = "llama3.2") -> Optional[str]:
    """Queries local Ollama instance if available."""
    try:
        url = "http://localhost:11434/api/generate"
        payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "")
    except Exception:
        return None

def call_gemini(prompt: str, api_key: str) -> Optional[str]:
    """Queries Gemini Flash API if GEMINI_API_KEY is present."""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}]
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"[!] Gemini API error: {e}")
    return None

@app.get("/api/search")
def search_documents(q: Optional[str] = "", program: str = "All", limit: int = 50):
    if not CHUNKS:
        return {"results": [], "total": 0, "message": "Index empty. Please run crawler.py first."}
    
    results = INDEX.search(q or "", program_filter=program, top_k=limit)
    return {
        "query": q,
        "program": program,
        "total": len(results),
        "results": results
    }

@app.post("/api/ask")
def ask_question(req: AskRequest):
    if not CHUNKS:
        raise HTTPException(status_code=503, detail="Search index is not loaded. Please run crawler.py to populate documents.")

    # 1. Retrieve most relevant context chunks
    retrieved = INDEX.search(req.question, program_filter=req.program, top_k=4)
    if not retrieved:
        return {
            "answer": "No matching policy sections found for this query in the current guide index. Try broadening your keywords.",
            "sources": []
        }

    context_str = "\n\n---\n\n".join([
        f"Document: {r['title']}\nProgram: {', '.join(r['programs'])}\nOfficial Link: {r['official_url']}\nExcerpt:\n{r['text']}"
        for r in retrieved
    ])

    program_name = "All San Diego County Benefits" if req.program == "All" else f"San Diego County {req.program} Program"

    system_prompt = f"""You are a helpful and precise policy navigation assistant for {program_name}.
Base your answers STRICTLY on the official policy manual excerpts provided below for {req.program}.
Do NOT extrapolate or cite regulations from other welfare programs.
Cite the specific chapter/article and document title for each rule.

OFFICIAL POLICY EXCERPTS ({req.program}):
{context_str}

USER QUESTION:
{req.question}

ANSWER WITH CITATIONS:"""

    answer = None
    provider_used = "heuristic"

    # Try Gemini if key is provided
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        answer = call_gemini(system_prompt, gemini_key)
        if answer:
            provider_used = "Gemini Flash"

    # Try local Ollama if no Gemini or if Ollama is preferred
    if not answer:
        answer = call_ollama(system_prompt)
        if answer:
            provider_used = "Local Ollama"

    # Fallback to direct citation synthesis if no LLM server is running
    if not answer:
        provider_used = "Direct Index Evidence"
        answer = (
            f"Here are the most relevant official policy rules found regarding '{req.question}':\n\n"
            + "\n\n".join([f"• **{r['title']}** ({', '.join(r['programs'])}):\n> {r['text'][:350]}..." for r in retrieved[:3]])
            + "\n\n*(Note: Configure an LLM provider such as local Ollama or set GEMINI_API_KEY to enable full conversational AI synthesis.)*"
        )

    return {
        "answer": answer,
        "provider": provider_used,
        "sources": [{
            "id": r["id"],
            "title": r["title"],
            "programs": r["programs"],
            "local_pdf_url": r.get("local_pdf_url", f"/pdfs/{r['id']}.pdf"),
            "official_url": r["official_url"],
            "published_on": r.get("published_on", ""),
            "snippet": r["text"][:250] + "..."
        } for r in retrieved]
    }

@app.get("/", response_class=HTMLResponse)
def index_page():
    html_file = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>San Diego County Benefits Search API is running.</h1>"
