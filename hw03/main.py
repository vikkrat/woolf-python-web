"""HTTP form application with durable JSON storage and Jinja2 rendering."""

import json
import logging
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import parse_qs, urlsplit

from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE = Path(__file__).resolve().parent
STORAGE = Path(os.getenv("STORAGE_DIR", str(BASE / "storage")))
LOCK = Lock()
TEMPLATES = Environment(loader=FileSystemLoader(BASE), autoescape=select_autoescape())


def read_messages():
    """Load persisted messages; never silently discard corrupted data."""
    path = STORAGE / "data.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_message(message):
    """Append under a lock and atomically replace the JSON file."""
    with LOCK:
        STORAGE.mkdir(parents=True, exist_ok=True)
        messages = read_messages()
        key = str(datetime.now())
        while key in messages:
            key = str(datetime.now())
        messages[key] = message
        temporary = STORAGE / "data.json.tmp"
        temporary.write_text(
            json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(STORAGE / "data.json")


class Handler(BaseHTTPRequestHandler):
    """Serve only explicitly allowed resources."""

    def respond(self, body, status=200, content_type="text/html; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/read":
            try:
                with LOCK:
                    messages = read_messages()
                body = TEMPLATES.get_template("read.html").render(messages=messages)
                self.respond(body.encode("utf-8"))
            except (OSError, ValueError):
                logging.exception("Cannot read messages")
                self.send_error(500, "Cannot read messages")
            return
        routes = {
            "/": "index.html",
            "/index.html": "index.html",
            "/message": "message.html",
            "/message.html": "message.html",
            "/style.css": "style.css",
            "/logo.png": "logo.png",
        }
        filename = routes.get(path, "error.html")
        content_type = {".css": "text/css", ".png": "image/png"}.get(
            Path(filename).suffix, "text/html; charset=utf-8"
        )
        self.respond(
            (BASE / filename).read_bytes(), 200 if path in routes else 404, content_type
        )

    def do_POST(self):
        if urlsplit(self.path).path != "/message":
            self.respond((BASE / "error.html").read_bytes(), 404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 65536:
                self.send_error(413, "Invalid message size")
                return
            if self.headers.get_content_type() != "application/x-www-form-urlencoded":
                self.send_error(415)
                return
            data = parse_qs(
                self.rfile.read(size).decode("utf-8"), keep_blank_values=True
            )
            message = {
                field: data.get(field, [""])[0].strip()
                for field in ("username", "message")
            }
            if not all(message.values()):
                self.send_error(400, "Username and message are required")
                return
            save_message(message)
        except (UnicodeError, ValueError):
            self.send_error(400, "Invalid form or storage data")
            return
        except OSError:
            logging.exception("Cannot save message")
            self.send_error(500)
            return
        self.send_response(303)
        self.send_header("Location", "/read")
        self.send_header("Content-Length", "0")
        self.end_headers()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with ThreadingHTTPServer(("0.0.0.0", 3000), Handler) as server:
        server.serve_forever()
