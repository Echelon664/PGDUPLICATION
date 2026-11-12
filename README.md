# SDCounty HHSA Program Guide

A fast, searchable policy engine and AI assistant for the County of San Diego Health and Human Services Agency (HHSA) public guides:
* **CalFresh (SNAP)** — [Folder 542](https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=542)
* **CalWORKs (TANF)** — [Folder 448](https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=448)
* **Medi-Cal (Medicaid)** — [Folder 599](https://file.sandiegocounty.gov/HHSAPublicSite/Section?FolderId=599)

---

## Features

1. **Local Offline PDF Serving**: Every PDF is stored locally in `data/pdfs/` and served directly through the web application (`/pdfs/<id>.pdf`). Users view documents immediately in their browser without redirecting to or depending on the County of San Diego website.
2. **Dual Search Modes**:
   * **Ask AI (RAG)**: Natural language question-answering with citations to official manual chapters and documents.
   * **Policy Search (SQLite FTS5 BM25)**: Instant keyword, phrase, and code lookup (e.g. `63-151`, `SAR 7`, `IRT`) with Porter stemming, section-number matching, and acronym expansion (`WTW`, `ABAD`, `SUA`, `SNAP`, `Medicaid`).
3. **Program Filtering**: Filter searches across All Programs, CalFresh only, CalWORKs only, or Medi-Cal only.
4. **Official Links & Disclaimers**: Includes secondary links to the County's public portal for reference, with clear disclaimers that this is an independent community reference tool.
5. **Zero Heavy Infrastructure**: Built with pure Python standard library support (`server.py`) and FastAPI (`app.py`), ready for 1-click cloud deployment.

---

## Project Structure

```
sd-benefits-search/
├── app.py                # FastAPI server (Search API, AI Ask API, Web Frontend)
├── crawler.py            # Automated crawler for SD County OutSystems portal
├── indexer.py            # Text chunker and legacy in-memory BM25 fallback
├── search_engine.py      # SQLite FTS5 index, query layer, and ranking
├── evaluate_search.py    # Recall@5 / MRR benchmark: BM25 vs FTS5
├── data/
│   ├── documents.json    # Crawled policy documents and metadata
│   └── search.db         # Generated FTS5 index (ignored by git)
├── templates/
│   └── index.html        # Responsive web interface with official disclaimers
├── Dockerfile            # Container configuration for public cloud deployment
└── requirements.txt      # Python dependencies
```

---

## Quickstart (Local)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. (Optional) Run Crawler
To fetch or refresh live documents from the San Diego County portal:
```bash
python3 crawler.py
```

### 3. Build the Search Index (Optional)
The FTS5 index builds automatically on first search. To rebuild it and run sample queries:
```bash
python3 search_engine.py
```
To compare the legacy BM25 engine with FTS5:
```bash
python3 evaluate_search.py
```

### 4. Start the Web Server
```bash
uvicorn app:app --reload --port 8000
```
Open your browser to [http://localhost:8000](http://localhost:8000).

---

## Search Engine

`search_engine.py` uses SQLite FTS5 from the Python standard library. It builds
`data/search.db` from `data/documents.json` and rebuilds automatically when the
documents file changes. The query layer adds:

* Porter stemming (`student` / `students`, `eligibility` / `eligible`)
* Exact and prefix section-code matching (`63-151`, `10-005`)
* Program and acronym expansion (`WTW`, `ABAD`, `SUA`, `SAR`, `SNAP`, `Medicaid`)
* Phrase queries, per-document deduplication, and title phrase boosts

No extra services or Python packages are required.

---

## Enabling AI Answers

### Local Ollama (100% Free & Local)
Install [Ollama](https://ollama.ai) and pull a fast model:
```bash
ollama run llama3.2:3b
```
The FastAPI backend will automatically detect and query your local Ollama instance on port 11434.

---

## Public Web Hosting Deployment

The app ships in a single container that builds the search index automatically
on first request. The `data/pdfs/` folder and `data/documents.json` are baked
into the image; `data/search.db` is generated at startup (and git-ignored).

### Build and run locally

```bash
docker compose up --build
# or without compose:
docker build -t sdcounty-hhsa .
docker run -d -p 8000:8000 --restart unless-stopped sdcounty-hhsa
```

The container listens on `$PORT` (default 8000) and exposes a `/health`
endpoint for orchestrator health checks.

### Hosting platforms (fastest)

Any platform that builds a Dockerfile works out of the box:

* **Railway** — `railway up` or link the repo; it builds the Dockerfile and
  issues an HTTPS URL.
* **Render** — new **Web Service** → **Build and Deploy from a Git repo**,
  runtime **Docker**; it reads the Dockerfile automatically.
* **Fly.io** — `fly launch` (pick the existing Dockerfile) then `fly deploy`;
  gives a global edge + automatic TLS.

For all three: no start command is needed — the Dockerfile `CMD` is used. Make
sure the service port is set to **8000** (or set the `PORT` env var).

### Self-host on a $4–6 VPS (Hetzner / DigitalOcean / Oracle)

```bash
# on the server
git clone <repo-url> && cd <repo>
docker build -t sdcounty-hhsa .
docker run -d -p 8000:8000 --restart unless-stopped --name hhsa sdcounty-hhsa
```

Then put HTTPS in front with Caddy (one line):

```bash
# Caddyfile
your-domain.com {
    reverse_proxy localhost:8000
}
```

Run Caddy in a container (`docker run -d -p 80:80 -p 443:443 -v $PWD/Caddyfile:/etc/caddy/Caddyfile caddy`)
and it provisions Let's Encrypt certificates automatically.

### Notes for production

* The bundled PDFs and documents are static data; rebuild the image when
  `data/` changes. The search index always rebuilds from `documents.json`.
* The "Ask AI" feature needs a local [Ollama](https://ollama.ai) instance. When
  deploying to a cloud host, run Ollama separately and set
  `OLLAMA_HOST`/point the backend at it, or keep using the built-in
  "Direct Manual Evidence" fallback (no LLM required).
* Single-process uvicorn is fine for this workload. For heavier traffic, run
  multiple workers (`uvicorn app:app --workers 4`) behind a load balancer; the
  SQLite index is read-only per process.
