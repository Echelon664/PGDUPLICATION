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

When AI_PROVIDER is unset/disabled, generate_answer returns None and the caller
falls back to the built-in "Direct Manual Evidence" answer.
"""

import json
import os
import urllib.request
from typing import Optional


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
