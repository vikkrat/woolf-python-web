"""Password hashing and purpose-bound expiring JWT credentials."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi import HTTPException
from pwdlib import PasswordHash

from app.config import settings

password_hash = PasswordHash.recommended()


def make_token(user, purpose="access", minutes=None):
    """Sign a token bound to an account, purpose and credential version."""
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user.id),
            "purpose": purpose,
            "version": user.token_version,
            "iat": now,
            "exp": now + timedelta(minutes=minutes or settings.access_minutes),
            "jti": str(uuid4()),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )


def decode_token(token, purpose="access"):
    """Reject expired, malformed or wrong-purpose credentials."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={"require": ["sub", "exp", "iat", "purpose", "version", "jti"]},
        )
        if payload["purpose"] != purpose or not str(payload["sub"]).isdigit():
            raise ValueError("Wrong token purpose or subject")
        if not isinstance(payload["version"], int):
            raise ValueError("Invalid token version")
        return payload
    except (jwt.PyJWTError, ValueError) as error:
        raise HTTPException(
            401, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"}
        ) from error
