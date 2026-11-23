"""Authenticated request dependencies with Redis user caching."""

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from redis.exceptions import RedisError

from app import services
from app.database import get_db
from app.models import User
from app.security import decode_token

oauth2 = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token=Depends(oauth2), db=Depends(get_db)):
    """Read the account from Redis first; populate only on cache misses.

    Redis failure fails closed rather than accepting possibly revoked tokens.
    Account updates invalidate the cache. Entries also expire after 60 seconds.
    """
    payload = decode_token(token)
    try:
        user = services.cached_user(payload["sub"])
        if user is None:
            user = db.get(User, int(payload["sub"]))
            if user:
                services.cache_user(user)
    except RedisError as error:
        raise HTTPException(503, "Authorization cache unavailable") from error
    if not user or not user.verified or user.token_version != payload["version"]:
        raise HTTPException(
            401, "Invalid credentials", headers={"WWW-Authenticate": "Bearer"}
        )
    return user
