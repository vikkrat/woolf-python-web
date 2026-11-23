"""Exercise real HTTP routing, form encoding, persistence and escaping."""

import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlencode

import main


def test_http_form_and_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "STORAGE", tmp_path)
    with ThreadingHTTPServer(("127.0.0.1", 0), main.Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        connection = HTTPConnection("127.0.0.1", server.server_port)
        try:
            for path, expected in [
                ("/", 200),
                ("/message", 200),
                ("/style.css", 200),
                ("/logo.png", 200),
                ("/missing", 404),
                ("/../main.py", 404),
            ]:
                connection.request("GET", path)
                response = connection.getresponse()
                assert response.status == expected
                response.read()
            for message in ["Привіт & + =", "<script>alert(1)</script>"]:
                connection.request(
                    "POST",
                    "/message",
                    urlencode({"username": "Олена", "message": message}),
                    {"Content-Type": "application/x-www-form-urlencoded"},
                )
                response = connection.getresponse()
                assert response.status == 303
                response.read()
            saved = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
            assert len(saved) == 2
            assert next(iter(saved.values()))["message"] == "Привіт & + ="
            connection.request("GET", "/read")
            response = connection.getresponse()
            assert response.status == 200
            body = response.read().decode()
            assert "&lt;script&gt;" in body
            assert "<script>" not in body
        finally:
            connection.close()
            server.shutdown()
            thread.join()
