"""Configurable AI answer backend.

Select a provider with the AI_PROVIDER environment variable:

    AI_PROVIDER=ollama   # local Ollama (default http://localhost:11434)
    AI_PROVIDER=openai   # any OpenAI-compatible chat/completions API

Environment variables:

    AI_PROVIDER   ollama | openai | none (default: none)
    AI_BASE_URL   override the provider base URL
    AI_MODEL      model name (default: llama3.2 for ollama, gpt-4o-mini for openai)
    AI_API_KEY    required for the openai provider
    AI_TIMEOUT    request timeout in seconds (default: 60)

Limits on the public /api/ask endpoint (LLM calls only; the built-in evidence
answer is always available):

    AI_RATE_LIMIT_PER_MIN         LLM calls per client per minute (default: 6)
    AI_RATE_LIMIT_GLOBAL_PER_MIN  LLM calls per minute across all clients (default: 30)
    AI_MAX_QUESTION_CHARS         longest accepted question (default: 500)

When AI_PROVIDER is unset/disabled, generate_answer returns None and the caller
falls back to the built-in "Direct Manual Evidence" answer.
"""

import json
import os
import threading
import time
import urllib.request
from collections import deque
from typing import Any, Deque, Dict, List, Optional

PROGRAMS = ("All", "CalFresh", "CalWORKs", "Medi-Cal")

# Each source excerpt sent to the LLM is capped so one long document cannot
# blow up the prompt.
MAX_EXCERPT_CHARS = 1500
MAX_SOURCES = 4


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def provider_label() -> str:
    provider = _env("AI_PROVIDER", "none").lower()
    if provider == "ollama":
        return "Local Ollama"
    if provider in ("openai", "openai-compatible", "groq", "together", "custom"):
        base = _env("AI_BASE_URL", "https://api.openai.com/v1")
        return "OpenAI" if "openai.com" in base else "Hosted LLM"
    return "none"


def generate_answer(prompt: str, model: Optional[str] = None) -> Optional[str]:
    provider = _env("AI_PROVIDER", "none").lower()
    if provider in ("", "none", "off", "false"):
        return None

    model = model or _env("AI_MODEL") or None
    try:
        timeout = float(_env("AI_TIMEOUT", "60") or "60")
    except ValueError:
        timeout = 60.0

    try:
        if provider == "ollama":
            return _ollama(prompt, model or "llama3.2", timeout)
        if provider in ("openai", "openai-compatible", "groq", "together", "custom"):
            return _openai_chat(prompt, model or "gpt-4o-mini", timeout)
    except Exception as exc:  # keep the API up even if the LLM is down
        print(f"[ai] {provider} request failed: {exc}")
    return None


def _ollama(prompt: str, model: str, timeout: float) -> Optional[str]:
    base = _env("AI_BASE_URL", "http://localhost:11434").rstrip("/")
    url = base + "/api/generate"
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("response") or None


def _openai_chat(prompt: str, model: str, timeout: float) -> Optional[str]:
    api_key = _env("AI_API_KEY")
    if not api_key:
        print("[ai] AI_PROVIDER=openai but AI_API_KEY is empty")
        return None
    base = _env("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    url = base + "/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"] or None


def _env_int(name: str, default: int) -> int:
    try:
        return max(0, int(_env(name, str(default)) or default))
    except ValueError:
        return default


def max_question_chars() -> int:
    return _env_int("AI_MAX_QUESTION_CHARS", 500) or 500


class _RateLimiter:
    """Sliding one-minute window, per client and across all clients."""

    def __init__(self):
        self._lock = threading.Lock()
        self._global: Deque[float] = deque()
        self._clients: Dict[str, Deque[float]] = {}

    def allow(self, client_id: str) -> bool:
        per_client = _env_int("AI_RATE_LIMIT_PER_MIN", 6)
        overall = _env_int("AI_RATE_LIMIT_GLOBAL_PER_MIN", 30)
        now = time.monotonic()
        cutoff = now - 60.0
        with self._lock:
            while self._global and self._global[0] < cutoff:
                self._global.popleft()
            for key in [k for k, q in self._clients.items() if not q or q[-1] < cutoff]:
                del self._clients[key]
            mine = self._clients.setdefault(client_id, deque())
            while mine and mine[0] < cutoff:
                mine.popleft()
            if len(mine) >= per_client or len(self._global) >= overall:
                return False
            mine.append(now)
            self._global.append(now)
            return True


_LIMITER = _RateLimiter()


def answer_question(engine, question: str, program: str = "All",
                    client_id: str = "unknown") -> Dict[str, Any]:
    """Shared /api/ask logic for app.py and server.py.

    Raises ValueError for an empty or over-long question.
    """
    question = (question or "").strip()
    if not question:
        raise ValueError("Missing question")
    limit = max_question_chars()
    if len(question) > limit:
        raise ValueError(f"Question is too long (limit {limit} characters)")
    if program not in PROGRAMS:
        program = "All"

    # Entries whose County document is not bundled have no text to cite.
    candidates = engine.search(question, program_filter=program, top_k=MAX_SOURCES * 3)
    retrieved: List[Dict[str, Any]] = [
        r for r in candidates if not r.get("source_missing") and (r.get("text") or "").strip()
    ][:MAX_SOURCES]
    if not retrieved:
        return {
            "answer": "No matching policy sections found for this question in the current guide index. Try broadening your keywords.",
            "provider": "none",
            "sources": [],
        }

    for r in retrieved:
        r["text"] = r["text"][:MAX_EXCERPT_CHARS]

    context_str = "\n\n---\n\n".join(
        f"Document: {r['title']}\nProgram: {', '.join(r['programs'])}\n"
        f"Official Link: {r['official_url']}\nExcerpt:\n{r['text']}"
        for r in retrieved
    )
    program_name = (
        "All San Diego County Benefits" if program == "All"
        else f"San Diego County {program} Program"
    )
    prompt = f"""You are a helpful and precise policy navigation assistant for {program_name}.
Base your answers STRICTLY on the official policy manual excerpts provided below for {program}.
Do NOT extrapolate or cite regulations from other welfare programs.
Cite the specific chapter/article and document title for each rule.

OFFICIAL POLICY EXCERPTS ({program}):
{context_str}

USER QUESTION:
{question}

ANSWER WITH CITATIONS:"""

    answer = None
    rate_limited = False
    if provider_label() != "none":
        if _LIMITER.allow(client_id):
            answer = generate_answer(prompt)
        else:
            rate_limited = True
    provider = provider_label() if answer else "Direct Manual Evidence"

    if not answer:
        note = (
            "*(The AI assistant is busy right now, so this is the direct evidence from the manuals. Try again in a minute.)*"
            if rate_limited else
            "*(Note: Set AI_PROVIDER (and AI_API_KEY for a hosted LLM) to enable full conversational AI synthesis.)*"
        )
        answer = (
            f"Here are the most relevant official policy rules found regarding '{question}':\n\n"
            + "\n\n".join(
                f"• **{r['title']}** ({', '.join(r['programs'])}):\n> {r['text'][:350]}..."
                for r in retrieved[:3]
            )
            + "\n\n" + note
        )

    return {
        "answer": answer,
        "provider": provider,
        "rate_limited": rate_limited,
        "sources": [{
            "id": r["id"],
            "title": r["title"],
            "programs": r["programs"],
            "local_pdf_url": r.get("local_pdf_url", ""),
            "official_url": r["official_url"],
            "published_on": r.get("published_on", ""),
            "summary": r.get("summary", ""),
            "snippet": r.get("summary") or (r["text"][:250] + "..."),
        } for r in retrieved],
    }
