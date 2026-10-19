#!/usr/bin/env python3
"""Serve ./Website on localhost with hot reload. Usage: python3 serve.py [port]"""
import os, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Website")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
# Injected into every HTML page: polls the newest mtime and reloads on change.
SNIPPET = b"""<script>(()=>{let m;setInterval(async()=>{try{const t=await(await fetch('/__mtime',{cache:'no-store'})).text();
if(m&&t!==m)location.reload();m=t}catch(e){}},500)})()</script>"""


def newest_mtime():
    return max(
        (os.stat(os.path.join(d, f)).st_mtime_ns for d, _, fs in os.walk(ROOT) for f in fs),
        default=0,
    )


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path == "/__mtime":
            return self._send(str(newest_mtime()).encode(), "text/plain")
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            path = os.path.join(path, "index.html")
        if path.endswith(".html") and os.path.isfile(path):
            with open(path, "rb") as f:
                body = f.read()
            i = body.lower().rfind(b"</body>")
            body = body[:i] + SNIPPET + body[i:] if i >= 0 else body + SNIPPET
            return self._send(body, "text/html; charset=utf-8")
        super().do_GET()

    def _send(self, body, ctype):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"http://localhost:{PORT}  (hot reload on, Ctrl+C to stop)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
