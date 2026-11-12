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
   * **Policy Search (BM25)**: Instant, sub-millisecond keyword and code lookup (e.g. `63-150`, `SAR 7`, `IRT`).
3. **Program Filtering**: Filter searches across All Programs, CalFresh only, CalWORKs only, or Medi-Cal only.
4. **Official Links & Disclaimers**: Includes secondary links to the County's public portal for reference, with clear disclaimers that this is an independent community reference tool.
5. **Zero Heavy Infrastructure**: Built with pure Python standard library support (`server.py`) and FastAPI (`app.py`), ready for 1-click cloud deployment.

---

## Project Structure

```
sd-benefits-search/
├── app.py                # FastAPI server (Search API, AI Ask API, Web Frontend)
├── crawler.py            # Automated crawler for SD County OutSystems portal
├── indexer.py            # Text chunker and BM25 indexer
├── data/
│   └── documents.json    # Crawled policy documents and metadata
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

### 3. Start the Web Server
```bash
uvicorn app:app --reload --port 8000
```
Open your browser to [http://localhost:8000](http://localhost:8000).

---

## Enabling AI Answers (Two Options)

### Option A: Local Ollama (100% Free & Local)
Install [Ollama](https://ollama.ai) and pull a fast model:
```bash
ollama run llama3.2:3b
```
The FastAPI backend will automatically detect and query your local Ollama instance on port 11434.

### Option B: Gemini 2.0 Flash API (Ultra-Fast & Cheap)
Set the environment variable:
```bash
export GEMINI_API_KEY="your-api-key"
uvicorn app:app --port 8000
```

---

## Public Web Hosting Deployment

### 1. Deploying to Railway or Render
1. Push this folder to a GitHub repository.
2. In [Railway.app](https://railway.app) or [Render.com](https://render.com), click **New Project** -> **Deploy from GitHub**.
3. Select Docker or Python runtime.
4. Set start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. (Optional) Add `GEMINI_API_KEY` in environment variables.

### 2. Deploying to a $4 VPS (Hetzner / DigitalOcean)
```bash
git clone <repo-url>
cd sd-benefits-search
docker build -t sd-benefits-search .
docker run -d -p 80:8000 --restart always --name benefits-search sd-benefits-search
```
