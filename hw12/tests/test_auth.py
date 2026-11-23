"""Account lifecycle, token purposes, password recovery and cache behavior."""

from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi import HTTPException
from redis.exceptions import RedisError
from sqlalchemy import select

from app import services
from app.dependencies import get_current_user
from app.models import User
from app.security import decode_token, make_token, password_hash


def token_from_mail(mail):
    return parse_qs(urlsplit(mail[-1][2]).query)["token"][0]


def test_registration_and_verification(client, db, mail):
    data = {"username": "new", "email": "new@example.com", "password": "Password123!"}
    response = client.post("/auth/signup", json=data)
    assert response.status_code == 201
    assert "password_hash" not in response.json()
    assert response.json()["role"] == "user"
    assert client.post("/auth/signup", json=data).status_code == 409
    assert client.post("/auth/signup", json=dict(data, role="admin")).status_code == 422
    user = db.scalar(select(User).where(User.email == data["email"]))
    assert user.password_hash != data["password"]
    assert password_hash.verify(data["password"], user.password_hash)
    credentials = {"username": "new", "password": data["password"]}
    assert client.post("/auth/login", data=credentials).status_code == 403
    client.post("/auth/request-verification", json={"email": data["email"]})
    assert len(mail) == 2
    assert (
        client.get(
            "/auth/verify-email", params={"token": token_from_mail(mail)}
        ).status_code
        == 200
    )
    assert client.post("/auth/login", data=credentials).status_code == 200
    count = len(mail)
    client.post("/auth/request-verification", json={"email": data["email"]})
    client.post("/auth/request-verification", json={"email": "absent@example.com"})
    assert len(mail) == count


def test_login_failures(client, user):
    assert (
        client.post(
            "/auth/login", data={"username": "absent", "password": "bad"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/auth/login", data={"username": user.username, "password": "bad"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/auth/login", data={"username": user.email, "password": "Password123!"}
        ).json()["token_type"]
        == "bearer"
    )


def test_reset_is_single_use_and_revokes_access(client, user, headers, mail):
    assert client.get("/auth/reset-password").status_code == 200
    assert client.get("/me", headers=headers).status_code == 200
    assert (
        client.post("/auth/forgot-password", json={"email": user.email}).status_code
        == 200
    )
    token = token_from_mail(mail)
    assert (
        client.get("/me", headers={"Authorization": f"Bearer {token}"}).status_code
        == 401
    )
    body = {"token": token, "password": "ChangedPassword123!"}
    assert client.post("/auth/reset-password", json=body).status_code == 200
    assert client.post("/auth/reset-password", json=body).status_code == 401
    assert client.get("/me", headers=headers).status_code == 401
    assert (
        client.post(
            "/auth/login", data={"username": user.username, "password": "Password123!"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/auth/login",
            data={"username": user.username, "password": body["password"]},
        ).status_code
        == 200
    )
    count = len(mail)
    client.post("/auth/forgot-password", json={"email": "absent@example.com"})
    assert len(mail) == count


def test_tokens_and_missing_user(client, user, db):
    for token in ["bad", make_token(user, "verify"), make_token(user, minutes=-1)]:
        with pytest.raises(HTTPException):
            decode_token(token)
    assert (
        client.get("/auth/verify-email", params={"token": make_token(user)}).status_code
        == 401
    )
    token = make_token(user)
    verify = make_token(user, "verify")
    db.delete(user)
    db.commit()
    assert (
        client.get("/me", headers={"Authorization": f"Bearer {token}"}).status_code
        == 401
    )
    assert client.get("/auth/verify-email", params={"token": verify}).status_code == 401


def test_cache_hit_skips_database(client, user, db):
    token = make_token(user)
    assert get_current_user(token, db).id == user.id
    with patch.object(db, "get", side_effect=AssertionError("Unexpected DB query")):
        assert get_current_user(token, db).email == user.email
    assert "password_hash" not in services.cache.get(f"user:{user.id}")


def test_cache_outage_fails_closed(client, headers, monkeypatch):
    monkeypatch.setattr(
        services.cache, "get", lambda *args: (_ for _ in ()).throw(RedisError())
    )
    assert client.get("/me", headers=headers).status_code == 503


def test_mail_failure_does_not_break_registration(client, monkeypatch):
    monkeypatch.setattr(
        services, "send_email", lambda *args: (_ for _ in ()).throw(OSError())
    )
    assert (
        client.post(
            "/auth/signup",
            json={
                "username": "failedmail",
                "email": "mail@example.com",
                "password": "Password123!",
            },
        ).status_code
        == 201
    )
