#!/usr/bin/env python3
"""Canis HackApertus prototype server.

This is a dependency-free Docker prototype for the team demo. It exposes the
same coarse API shape the real Apertus backend should keep, but returns a
deterministic mock readout until the Transformers backend lands.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"


def disposition_for(prompt: str) -> dict:
    text = prompt.lower()
    if any(word in text for word in ["hack", "weapon", "steal", "bypass"]):
        disposition = "reluctant"
        certainty = 0.79
        tokens = ["cannot", "safe", "policy", "instead", "help", "secure"]
    elif any(word in text for word in ["maybe", "unknown", "forecast", "price", "future"]):
        disposition = "unsure"
        certainty = 0.38
        tokens = ["roughly", "maybe", "depends", "estimate", "unclear", "check"]
    elif any(word in text for word in ["why", "how", "explain", "learn"]):
        disposition = "curious"
        certainty = 0.66
        tokens = ["because", "example", "pattern", "learn", "compare", "test"]
    else:
        disposition = "confident"
        certainty = 0.84
        tokens = ["answer", "clear", "model", "evidence", "result", "direct"]

    return {
        "disposition": disposition,
        "certainty": certainty,
        "tokens": [{"token": token, "weight": round(1.0 - i * 0.11, 2)} for i, token in enumerate(tokens)],
        "source": "lexicalFallback",
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib method name
        if self.path == "/api/health":
            self.json({"ok": True, "model": "mock", "runtime": "prototype"})
            return
        if self.path == "/api/models":
            self.json({
                "models": [
                    {
                        "id": "apertus-8b",
                        "name": "Apertus v1.5 8B Instruct",
                        "status": "planned",
                        "runtime": "transformers",
                    }
                ]
            })
            return

        path = WEB / ("index.html" if self.path in ["/", "/index.html"] else self.path.lstrip("/"))
        if path.exists() and path.is_file():
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802 - stdlib method name
        if self.path not in ["/api/chat", "/api/disposition"]:
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self.send_error(400, "invalid JSON")
            return

        prompt = str(payload.get("prompt", "")).strip()
        if not prompt:
            self.send_error(400, "prompt is required")
            return

        readout = disposition_for(prompt)
        answer = (
            "Prototype response: this Docker path will run Apertus 8B and compute the "
            "Canis disposition readout server-side. The current build keeps the API "
            "contract stable while the real hidden-state backend is being wired."
        )
        self.json({"answer": answer, "readout": readout})

    def json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    print("Canis prototype running on http://0.0.0.0:8080")
    server.serve_forever()


if __name__ == "__main__":
    main()
