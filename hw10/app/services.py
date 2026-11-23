"""Redis cache, rate limits, SMTP delivery and Cloudinary uploads."""

import json
import smtplib
from email.message import EmailMessage
from types import SimpleNamespace

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException
from redis import Redis
from redis.exceptions import RedisError

from app.config import settings

cache = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_timeout=3,
    socket_connect_timeout=3,
)


def cache_user(user):
    """Cache only authorization and public fields, never password hashes."""
    data = {
        key: getattr(user, key)
        for key in (
            "id",
            "username",
            "email",
            "verified",
            "role",
            "avatar",
            "token_version",
        )
    }
    cache.setex(f"user:{user.id}", settings.cache_seconds, json.dumps(data))


def cached_user(user_id):
    """Return the cached account or None on a cache miss."""
    value = cache.get(f"user:{user_id}")
    return SimpleNamespace(**json.loads(value)) if value else None


def invalidate_user(user_id):
    """Remove stale authorization data after any account mutation."""
    cache.delete(f"user:{user_id}")


def check_rate(user_id):
    """Apply an atomic Redis fixed-window limit shared across API workers."""
    script = """local n = redis.call('INCR', KEYS[1])
    if n == 1 then redis.call('EXPIRE', KEYS[1], 60) end
    return n"""
    try:
        count = cache.eval(script, 1, f"rate:me:{user_id}")
    except RedisError as error:
        raise HTTPException(503, "Rate limiter unavailable") from error
    if count > settings.me_limit:
        raise HTTPException(429, "Too many requests", headers={"Retry-After": "60"})


def send_email(email, subject, link):
    """Send a link through configured SMTP; local Compose uses Mailpit."""
    message = EmailMessage()
    message["From"], message["To"], message["Subject"] = (
        settings.mail_from,
        email,
        subject,
    )
    message.set_content(
        f"{subject}\n\n{link}\n\nIf you did not request this, ignore this email."
    )
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)


def upload_avatar(content, user_id):
    """Upload a bounded image to the account's fixed Cloudinary asset."""
    if not all(
        (
            settings.cloudinary_cloud_name,
            settings.cloudinary_api_key,
            settings.cloudinary_api_secret,
        )
    ):
        raise HTTPException(503, "Cloudinary is not configured")
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    result = cloudinary.uploader.upload(
        content,
        public_id=f"contacts/avatars/{user_id}",
        overwrite=True,
        resource_type="image",
        transformation=[{"width": 250, "height": 250, "crop": "fill"}],
    )
    return result["secure_url"]
