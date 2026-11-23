"""Authentication and avatar permissions for the homework 10 edition."""

from urllib.parse import parse_qs, urlsplit

from app import services


def test_signup_verify_login(client, mail):
    body = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "Password123!",
    }
    assert client.post("/auth/signup", json=body).status_code == 201
    assert client.post("/auth/signup", json=body).status_code == 409
    credentials = {"username": body["username"], "password": body["password"]}
    assert client.post("/auth/login", data=credentials).status_code == 403
    token = parse_qs(urlsplit(mail[-1][2]).query)["token"][0]
    assert client.get("/auth/verify-email", params={"token": token}).status_code == 200
    assert "access_token" in client.post("/auth/login", data=credentials).json()
    assert (
        client.post("/auth/login", data=dict(credentials, password="bad")).status_code
        == 401
    )


def test_regular_user_can_update_avatar(client, headers, monkeypatch):
    monkeypatch.setattr(
        services, "upload_avatar", lambda *args: "https://example.com/avatar.png"
    )
    result = client.patch(
        "/me/avatar",
        headers=headers,
        files={"file": ("avatar.png", b"image", "image/png")},
    )
    assert result.status_code == 200
    assert result.json()["avatar"] == "https://example.com/avatar.png"


def test_rate_limit(client, headers):
    for _ in range(10):
        assert client.get("/me", headers=headers).status_code == 200
    assert client.get("/me", headers=headers).status_code == 429
