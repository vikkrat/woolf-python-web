"""Check running local Compose stacks using real PostgreSQL, Redis and Mailpit.

Run after starting hw02, hw03, hw08, hw10 and hw12. Creates identifiable smoke
accounts/messages, deletes only contacts created by this run. Requires httpx.
"""

import re
import time
from uuid import uuid4

import httpx


def check_auth(port, mail_port, final=False):
    suffix = uuid4().hex[:10]
    email = f"smoke-{suffix}@example.com"
    password = "Smoke-test-password-123!"
    with httpx.Client(base_url=f"http://localhost:{port}", timeout=15) as client:
        response = client.post(
            "/auth/signup",
            json={"username": f"smoke{suffix}", "email": email, "password": password},
        )
        assert response.status_code == 201, response.text
        assert "password_hash" not in response.json()
        with httpx.Client(
            base_url=f"http://localhost:{mail_port}", timeout=15
        ) as mailbox:
            messages = mailbox.get("/api/v1/messages").json()["messages"]
            message = next(
                item
                for item in messages
                if any(recipient["Address"] == email for recipient in item["To"])
            )
            content = mailbox.get(f"/api/v1/message/{message['ID']}").json()["Text"]
            link = re.search(r"http://\S+", content).group(0)
            assert client.get(link).status_code == 200
            login = client.post(
                "/auth/login", data={"username": email, "password": password}
            )
            assert login.status_code == 200, login.text
            client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
            assert client.get("/me").json()["email"] == email
            body = {
                "first_name": "Smoke",
                "last_name": "Test",
                "email": email,
                "phone": "+123456",
                "birthday": "2000-01-01",
            }
            created = client.post("/contacts", json=body)
            assert created.status_code == 201, created.text
            identifier = created.json()["id"]
            assert len(client.get("/contacts", params={"q": email}).json()) == 1
            assert client.get("/contacts/birthdays").status_code == 200
            assert (
                client.put(
                    f"/contacts/{identifier}", json=dict(body, first_name="Updated")
                ).status_code
                == 200
            )
            assert client.delete(f"/contacts/{identifier}").status_code == 204
            avatar = client.patch(
                "/me/avatar", files={"file": ("a.png", b"image", "image/png")}
            )
            assert avatar.status_code == (403 if final else 503), avatar.text
            if final:
                assert (
                    client.post(
                        "/auth/forgot-password", json={"email": email}
                    ).status_code
                    == 200
                )
                messages = mailbox.get("/api/v1/messages").json()["messages"]
                reset = next(
                    item
                    for item in messages
                    if item["Subject"] == "Reset password"
                    and any(recipient["Address"] == email for recipient in item["To"])
                )
                content = mailbox.get(f"/api/v1/message/{reset['ID']}").json()["Text"]
                token = re.search(r"token=([^\s]+)", content).group(1)
                body = {"token": token, "password": "Replacement-password-123!"}
                assert client.post("/auth/reset-password", json=body).status_code == 200
                assert client.post("/auth/reset-password", json=body).status_code == 401
                assert client.get("/me").status_code == 401
    print(
        f"PASS {port}: SMTP verification, JWT, PostgreSQL CRUD, Redis, avatar authorization"
        + (", password reset" if final else "")
    )


def main():
    with httpx.Client(timeout=15) as client:
        response = client.get("http://localhost:8002/healthchecker")
        assert response.json() == {"message": "Welcome to FastAPI!"}, response.text
        assert "Перевірити БД" in client.get("http://localhost:8002").text
        print("PASS hw02: home page and database SELECT 1")
        message = f"Docker smoke {time.time()}"
        assert (
            client.post(
                "http://localhost:3000/message",
                data={"username": "Smoke", "message": message},
            ).status_code
            == 303
        )
        assert message in client.get("http://localhost:3000/read").text
        print("PASS hw03: HTTP form and persistent JSON")
        body = {
            "first_name": "Smoke",
            "last_name": "Test",
            "email": f"smoke-{uuid4().hex}@example.com",
            "phone": "+123456",
            "birthday": "2000-01-01",
        }
        created = client.post("http://localhost:8008/contacts", json=body)
        assert created.status_code == 201, created.text
        identifier = created.json()["id"]
        assert (
            client.get(f"http://localhost:8008/contacts/{identifier}").status_code
            == 200
        )
        assert (
            client.delete(f"http://localhost:8008/contacts/{identifier}").status_code
            == 204
        )
        print("PASS hw08: PostgreSQL contact CRUD")
    check_auth(8010, 8110)
    check_auth(8012, 8112, final=True)


if __name__ == "__main__":
    main()
