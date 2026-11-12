import os
from typing import Optional, List
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi.staticfiles import StaticFiles

from ai_backend import generate_answer, provider_label
from search_engine import get_engine

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

ENGINE = get_engine()
print(f"[✓] Search engine ready: {ENGINE.stats()}")

class AskRequest(BaseModel):
    question: str
    program: Optional[str] = "All"
    model_provider: Optional[str] = "auto" # 'ollama', 'mock'

@app.get("/api/search")
def search_documents(q: Optional[str] = "", program: str = "All", limit: int = 50):
    results = ENGINE.search(q or "", program_filter=program, top_k=limit)
    return {
        "query": q,
        "program": program,
        "total": len(results),
        "results": results
    }

@app.post("/api/ask")
def ask_question(req: AskRequest):
    # 1. Retrieve most relevant context chunks
    retrieved = ENGINE.search(req.question, program_filter=req.program, top_k=4)
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

    answer = generate_answer(system_prompt)
    provider_used = provider_label() if answer else "Direct Index Evidence"

    # Fallback to direct citation synthesis when no LLM is configured/reachable.
    if not answer:
        answer = (
            f"Here are the most relevant official policy rules found regarding '{req.question}':\n\n"
            + "\n\n".join([f"• **{r['title']}** ({', '.join(r['programs'])}):\n> {r['text'][:350]}..." for r in retrieved[:3]])
            + "\n\n*(Note: Set AI_PROVIDER (and AI_API_KEY for a hosted LLM) to enable full conversational AI synthesis.)*"
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
