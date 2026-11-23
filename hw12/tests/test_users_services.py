"""Rate limits, role checks and external-service adapters."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from redis.exceptions import RedisError

from app import services
from app.config import settings


def test_rate_limit(client, headers):
    for _ in range(settings.me_limit):
        assert client.get("/me", headers=headers).status_code == 200
    assert client.get("/me", headers=headers).status_code == 429


def test_rate_outage(client, monkeypatch):
    monkeypatch.setattr(
        services.cache, "eval", lambda *args: (_ for _ in ()).throw(RedisError())
    )
    with pytest.raises(HTTPException) as error:
        services.check_rate(1)
    assert error.value.status_code == 503


def test_avatar_permissions_and_updates(client, user, db, headers, monkeypatch):
    image = {"file": ("avatar.png", b"fake-png", "image/png")}
    assert client.patch("/me/avatar", files=image, headers=headers).status_code == 403
    user.role = "admin"
    db.commit()
    services.invalidate_user(user.id)
    monkeypatch.setattr(
        services,
        "upload_avatar",
        lambda content, identifier: "https://example.com/avatar.png",
    )
    response = client.patch("/me/avatar", files=image, headers=headers)
    assert response.status_code == 200
    assert (
        client.get("/me", headers=headers).json()["avatar"]
        == "https://example.com/avatar.png"
    )
    assert (
        client.patch(
            "/me/avatar", files={"file": ("a.txt", b"x", "text/plain")}, headers=headers
        ).status_code
        == 415
    )
    assert (
        client.patch(
            "/me/avatar", files={"file": ("a.png", b"", "image/png")}, headers=headers
        ).status_code
        == 413
    )
    assert (
        client.patch(
            "/me/avatar",
            files={"file": ("a.png", b"x" * (2 * 1024 * 1024 + 1), "image/png")},
            headers=headers,
        ).status_code
        == 413
    )
    monkeypatch.setattr(
        services, "upload_avatar", lambda *args: (_ for _ in ()).throw(ValueError())
    )
    assert client.patch("/me/avatar", files=image, headers=headers).status_code == 502


def test_cloudinary_adapter(monkeypatch):
    with pytest.raises(HTTPException) as error:
        services.upload_avatar(b"image", 1)
    assert error.value.status_code == 503
    for key in ("cloudinary_cloud_name", "cloudinary_api_key", "cloudinary_api_secret"):
        monkeypatch.setattr(settings, key, "test")
    with patch(
        "app.services.cloudinary.uploader.upload",
        return_value={"secure_url": "https://example.com/a.png"},
    ) as upload:
        assert services.upload_avatar(b"image", 7) == "https://example.com/a.png"
        assert upload.call_args.kwargs["public_id"] == "contacts/avatars/7"


def test_smtp_adapter(monkeypatch):
    monkeypatch.setattr(settings, "smtp_starttls", True)
    monkeypatch.setattr(settings, "smtp_user", "test-user")
    smtp = MagicMock()
    with patch("app.services.smtplib.SMTP") as constructor:
        constructor.return_value.__enter__.return_value = smtp
        services.send_email(
            "recipient@example.com", "Verify", "https://example.com/token"
        )
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once()
    assert smtp.send_message.call_args.args[0]["To"] == "recipient@example.com"
