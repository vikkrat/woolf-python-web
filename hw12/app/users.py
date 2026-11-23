"""Current-user endpoint and role-protected avatar updates."""

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from redis.exceptions import RedisError

from app import services
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import UserOutput

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserOutput)
def me(user=Depends(get_current_user)):
    """Get the current account with a shared per-user request limit."""
    services.check_rate(user.id)
    return user


@router.patch("/me/avatar", response_model=UserOutput)
def avatar(file: UploadFile, db=Depends(get_db), user=Depends(get_current_user)):
    """Allow only administrators to update their own avatar via Cloudinary."""
    if user.role != "admin":
        raise HTTPException(403, "Administrator role required")
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(415, "Use JPEG, PNG or WebP")
    content = file.file.read(2 * 1024 * 1024 + 1)
    if not content or len(content) > 2 * 1024 * 1024:
        raise HTTPException(413, "Image must be between 1 byte and 2 MiB")
    try:
        url = services.upload_avatar(content, user.id)
    except HTTPException:
        raise
    except Exception as error:
        logging.getLogger(__name__).warning("Avatar provider rejected upload")
        raise HTTPException(502, "Avatar upload failed") from error
    account = db.get(User, user.id)
    account.avatar = url
    db.commit()
    try:
        services.invalidate_user(user.id)
    except RedisError as error:
        raise HTTPException(503, "Authorization cache unavailable") from error
    return account
