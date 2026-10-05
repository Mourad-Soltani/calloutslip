# Mourad.Soltani — CalloutSlip HTTP app
"""Stdlib HTTP server for CalloutSlip. No third-party dependencies."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from src.quote import QuoteError, build_quote


ROOT = Path(__file__).resolve().parent
INDEX = (ROOT / "web" / "index.html").read_text(encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            payload = json.dumps({"status": "ok", "service": "calloutslip", "author": "Mourad.Soltani"}).encode()
            self._send(200, payload, "application/json")
            return
        if path in {"/", "/index.html"}:
            self._send(200, INDEX.encode(), "text/html; charset=utf-8")
            return
        self._send(404, b'{"error":"not found"}', "application/json")

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/quote":
            self._send(404, b'{"error":"not found"}', "application/json")
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode() or "{}")
            quote = build_quote(data)
        except QuoteError as exc:
            self._send(400, json.dumps({"error": str(exc)}).encode(), "application/json")
            return
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            self._send(400, json.dumps({"error": f"invalid payload: {exc}"}).encode(), "application/json")
            return
        self._send(200, json.dumps(quote.as_dict()).encode(), "application/json")


def serve(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"CalloutSlip listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    serve()
