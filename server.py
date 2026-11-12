import os
import json
import urllib.parse
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

from search_engine import get_engine

def call_ollama(prompt: str, model: str = "llama3.2") -> str:
    try:
        url = "http://localhost:11434/api/generate"
        payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "")
    except Exception:
        return ""

PORT = 8000
ENGINE = get_engine()

def get_index():
    # The engine rebuilds data/search.db automatically when documents.json changes.
    return ENGINE

class BenefitsHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            return
        if path.startswith("/pdfs/"):
            raw_filename = os.path.basename(path)
            filename = urllib.parse.unquote(raw_filename)
            pdf_path = os.path.join(os.path.dirname(__file__), "data", "pdfs", filename)
            if not os.path.exists(pdf_path) and os.path.exists(os.path.join(os.path.dirname(__file__), "data", "pdfs", raw_filename)):
                pdf_path = os.path.join(os.path.dirname(__file__), "data", "pdfs", raw_filename)
            if os.path.exists(pdf_path) and filename.endswith(".pdf"):
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Length", str(os.path.getsize(pdf_path)))
                self.send_header("Content-Disposition", f"inline; filename=\"{filename}\"")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                return
        self.send_response(404)
        self.end_headers()
    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/pdfs/"):
            raw_filename = os.path.basename(path)
            filename = urllib.parse.unquote(raw_filename)
            pdf_path = os.path.join(os.path.dirname(__file__), "data", "pdfs", filename)
            if not os.path.exists(pdf_path) and os.path.exists(os.path.join(os.path.dirname(__file__), "data", "pdfs", raw_filename)):
                pdf_path = os.path.join(os.path.dirname(__file__), "data", "pdfs", raw_filename)
            if os.path.exists(pdf_path) and filename.endswith(".pdf"):
                with open(pdf_path, "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/pdf")
                    self.send_header("Content-Disposition", f"inline; filename=\"{filename}\"")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(f.read())
                return
            else:
                self._set_headers(404, "text/plain")
                self.wfile.write(b"Local PDF file not found.")
                return

        if path == "/" or path == "/index.html":
            html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
            if os.path.exists(html_path):
                with open(html_path, "rb") as f:
                    self._set_headers(200, "text/html; charset=utf-8")
                    self.wfile.write(f.read())
            else:
                self._set_headers(404, "text/plain")
                self.wfile.write(b"templates/index.html not found.")
            return

        if path == "/api/search":
            query_params = urllib.parse.parse_qs(parsed.query)
            q = query_params.get("q", [""])[0]
            program = query_params.get("program", ["All"])[0]
            limit = int(query_params.get("limit", [250])[0])

            results = get_index().search(q, program_filter=program, top_k=limit)
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "query": q,
                "program": program,
                "total": len(results),
                "results": results
            }).encode("utf-8"))
            return

        self._set_headers(404, "text/plain")
        self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/ask":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body) if body else {}

            question = data.get("question", "").strip()
            program = data.get("program", "All")

            if not question:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing question"}).encode("utf-8"))
                return

            retrieved = get_index().search(question, program_filter=program, top_k=4)
            if not retrieved:
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "answer": "No matching policy sections found in the current index.",
                    "sources": []
                }).encode("utf-8"))
                return

            context_str = "\n\n---\n\n".join([
                f"Document: {r.get('title', '')}\nProgram: {', '.join(r.get('programs', []))}\nOfficial Link: {r.get('official_url', '')}\nExcerpt:\n{r.get('matched_excerpt') or r.get('text') or r.get('summary', '')}"
                for r in retrieved
            ])

            program_name = "All San Diego County Benefits" if program == "All" else f"San Diego County {program} Program (Official Folder)"

            system_prompt = f"""You are a helpful and precise policy navigation assistant for {program_name}.
Base your answers STRICTLY on the official policy manual excerpts provided below for {program}.
Do NOT extrapolate or cite regulations from other welfare programs.
Cite the specific chapter/article and document title for each rule.

OFFICIAL POLICY EXCERPTS ({program}):
{context_str}

USER QUESTION:
{question}

ANSWER WITH CITATIONS:"""

            answer = None
            provider = "heuristic"

            answer = call_ollama(system_prompt)
            if answer:
                provider = "Local Ollama"

            if not answer:
                provider = "Direct Manual Evidence"
                answer = (
                    f"Relevant policy rules regarding '{question}':\n\n"
                    + "\n\n".join([f"• **{r['title']}** ({', '.join(r['programs'])}):\n> {r['text'][:350]}..." for r in retrieved[:3]])
                    + "\n\n*(Connect Ollama locally for full conversational synthesis.)*"
                )

            self._set_headers(200)
            self.wfile.write(json.dumps({
                "answer": answer,
                "provider": provider,
                "sources": [{
                    "id": r["id"],
                    "title": r["title"],
                    "programs": r["programs"],
                    "local_pdf_url": r.get("local_pdf_url", f"/pdfs/{r['id']}.pdf"),
                    "official_url": r["official_url"],
                    "published_on": r.get("published_on", ""),
                    "summary": r.get("summary", ""),
                    "snippet": r.get("summary") or (r["text"][:250] + "...")
                } for r in retrieved]
            }).encode("utf-8"))
            return

        self._set_headers(404, "text/plain")
        self.wfile.write(b"Not Found")

def run():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, BenefitsHandler)
    print(f"[✓] Zero-dependency benefits server running at http://localhost:{PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
