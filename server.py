import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

import county_sync
from ai_backend import answer_question
from search_engine import get_engine

PORT = int(os.environ.get("PORT", "8000"))
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
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Admin-Token")
        self.end_headers()

    def _send_json(self, status, payload):
        self._set_headers(status)
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def _read_json_body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        if length > 16384:
            raise ValueError("Request too large")
        body = self.rfile.read(length).decode("utf-8") if length else ""
        data = json.loads(body) if body else {}
        if not isinstance(data, dict):
            raise ValueError("Body must be a JSON object")
        return data

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

        if path == "/sync":
            with open(os.path.join(os.path.dirname(__file__), "templates", "sync.html"), "rb") as f:
                self._set_headers(200, "text/html; charset=utf-8")
                self.wfile.write(f.read())
            return

        if path == "/api/sync/status":
            self._send_json(200, county_sync.status())
            return

        if path == "/api/sync/report":
            report = county_sync.load_report()
            if report is None:
                self._send_json(404, {"detail": "No scan has been run yet"})
            else:
                self._send_json(200, report)
            return

        if path == "/api/search":
            query_params = urllib.parse.parse_qs(parsed.query)
            q = query_params.get("q", [""])[0]
            program = query_params.get("program", ["All"])[0]
            try:
                limit = max(1, min(int(query_params.get("limit", [250])[0]), 250))
            except ValueError:
                limit = 250
            q = q[:300]

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
        if parsed.path == "/api/sync/scan":
            # A scan downloads hundreds of files from the County, so it is admin-only.
            try:
                mode = str(self._read_json_body().get("mode", "quick"))
            except ValueError as exc:
                self._send_json(400, {"detail": str(exc)})
                return
            if not county_sync.admin_enabled():
                self._send_json(503, {"detail": "Scans are disabled: set ADMIN_TOKEN on the server"})
            elif not county_sync.check_admin(self.headers.get("X-Admin-Token")):
                self._send_json(403, {"detail": "Invalid admin token"})
            elif mode not in ("quick", "full"):
                self._send_json(400, {"detail": "mode must be 'quick' or 'full'"})
            elif not county_sync.start_scan(mode):
                self._send_json(409, {"detail": "A scan is already running"})
            else:
                self._send_json(200, {"started": True, "mode": mode})
            return

        if parsed.path == "/api/ask":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
            except ValueError:
                content_length = 0
            if content_length > 16384:
                self._set_headers(413)
                self.wfile.write(json.dumps({"error": "Request too large"}).encode("utf-8"))
                return
            try:
                body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(body) if body else {}
                if not isinstance(data, dict):
                    raise ValueError("Body must be a JSON object")
                result = answer_question(
                    get_index(),
                    str(data.get("question", "")),
                    str(data.get("program", "All")),
                    self.client_address[0],
                )
            except ValueError as exc:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": str(exc)}).encode("utf-8"))
                return

            self._set_headers(200)
            self.wfile.write(json.dumps(result).encode("utf-8"))
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
