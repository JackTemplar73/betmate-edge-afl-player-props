#!/usr/bin/env python3
"""Serve BetMate Edge static files and proxy refresh endpoints."""

from __future__ import annotations

import http.client
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HOST = os.environ.get("BETMATE_PUBLIC_HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", os.environ.get("BETMATE_PUBLIC_PORT", "8000")))
REFRESH_HOST = os.environ.get("BETMATE_REFRESH_HOST", "127.0.0.1")
REFRESH_PORT = int(os.environ.get("BETMATE_REFRESH_PORT", "8765"))
PROXY_PATHS = {"/health", "/refresh"}


class BetmatePublicHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str | None = None, **kwargs) -> None:
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in PROXY_PATHS:
            self._proxy_request("GET")
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if self.path in PROXY_PATHS:
            self._proxy_request("POST")
            return
        self.send_error(405, "Method not allowed")

    def do_OPTIONS(self) -> None:  # noqa: N802
        if self.path in PROXY_PATHS:
            self._proxy_request("OPTIONS")
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _proxy_request(self, method: str) -> None:
        body = None
        headers: dict[str, str] = {}
        if method in {"POST", "PUT", "PATCH"}:
            length = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(length) if length else None
        for key in ("Content-Type", "Authorization"):
            value = self.headers.get(key)
            if value:
                headers[key] = value

        conn = http.client.HTTPConnection(REFRESH_HOST, REFRESH_PORT, timeout=120)
        try:
            conn.request(method, self.path, body=body, headers=headers)
            response = conn.getresponse()
            payload = response.read()
            self.send_response(response.status)
            for key, value in response.getheaders():
                lower = key.lower()
                if lower in {"transfer-encoding", "connection", "server", "date", "content-length"}:
                    continue
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        finally:
            conn.close()


def main() -> None:
    handler = partial(BetmatePublicHandler, directory=str(ROOT))
    server = ThreadingHTTPServer((HOST, PORT), handler)
    print(f"BetMate Edge public server listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    os.chdir(ROOT)
    main()
