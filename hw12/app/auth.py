"""Account registration, email verification, authentication and recovery."""

import logging
import smtplib

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from redis.exceptions import RedisError
from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError

from app import services
from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import EmailRequest, ResetPassword, Signup, TokenOutput, UserOutput
from app.security import decode_token, make_token, password_hash

router = APIRouter(prefix="/auth", tags=["authentication"])
LOG = logging.getLogger(__name__)
GENERIC_MESSAGE = {"message": "If the account is eligible, an email has been sent."}


def deliver(user, purpose):
    """Deliver a short-lived purpose-bound link without logging the token."""
    token = make_token(user, purpose, 30)
    path = "verify-email" if purpose == "verify" else "reset-password"
    try:
        services.send_email(
            user.email,
            "Verify email" if purpose == "verify" else "Reset password",
            f"{settings.public_url}/auth/{path}?token={token}",
        )
    except (OSError, smtplib.SMTPException):
        LOG.warning("Email delivery failed; user may request another email")


@router.post("/signup", status_code=201, response_model=UserOutput)
def signup(data: Signup, db=Depends(get_db)):
    """Create an unverified account and send email confirmation."""
    user = User(
        username=data.username,
        email=str(data.email).lower(),
        password_hash=password_hash.hash(data.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(409, "Email or username already registered") from error
    db.refresh(user)
    deliver(user, "verify")
    return user


@router.post("/login", response_model=TokenOutput)
def login(form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    """Authenticate form-body username/email and password, returning access_token."""
    user = db.scalar(
        select(User).where(
            or_(User.username == form.username, User.email == form.username.lower())
        )
    )
    if user is None or not password_hash.verify(form.password, user.password_hash):
        raise HTTPException(
            401, "Invalid credentials", headers={"WWW-Authenticate": "Bearer"}
        )
    if not user.verified:
        raise HTTPException(403, "Verify your email first")
    return {"access_token": make_token(user), "token_type": "bearer"}


@router.get("/verify-email")
def verify_email(token: str, db=Depends(get_db)):
    """Verify the account identified by a valid email-only token."""
    payload = decode_token(token, "verify")
    user = db.get(User, int(payload["sub"]))
    if not user or user.token_version != payload["version"]:
        raise HTTPException(401, "Invalid token")
    user.verified = True
    db.commit()
    try:
        services.invalidate_user(user.id)
    except RedisError as error:
        raise HTTPException(503, "Authorization cache unavailable") from error
    return {"message": "Email verified"}


@router.post("/request-verification")
def request_verification(data: EmailRequest, db=Depends(get_db)):
    """Resend verification without revealing whether an address is registered."""
    user = db.scalar(select(User).where(User.email == str(data.email).lower()))
    if user and not user.verified:
        deliver(user, "verify")
    return GENERIC_MESSAGE


@router.post("/forgot-password")
def forgot_password(data: EmailRequest, db=Depends(get_db)):
    """Send a reset link for verified accounts without exposing account existence."""
    user = db.scalar(select(User).where(User.email == str(data.email).lower()))
    if user and user.verified:
        deliver(user, "reset")
    return GENERIC_MESSAGE


@router.get("/reset-password", response_class=HTMLResponse, include_in_schema=False)
def reset_form():
    """Show the email-link password form without interpolating untrusted input."""
    return HTMLResponse(
        """<!doctype html><html lang="uk"><meta charset="utf-8">
    <title>Новий пароль</title><h1>Встановіть новий пароль</h1>
    <form id="reset"><label>Новий пароль <input id="password" type="password"
    minlength="8" maxlength="128" required autocomplete="new-password"></label>
    <button>Зберегти</button></form><p id="result" role="status"></p>
    <script>
    document.getElementById('reset').addEventListener('submit', async event => {
      event.preventDefault();
      const response = await fetch('/auth/reset-password', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({token: new URLSearchParams(location.search).get('token'),
          password: document.getElementById('password').value})});
      const data = await response.json();
      document.getElementById('result').textContent = response.ok
        ? 'Пароль змінено. Увійдіть з новим паролем.' : JSON.stringify(data.detail);
    });
    </script></html>""",
        headers={"Referrer-Policy": "no-referrer", "Cache-Control": "no-store"},
    )


@router.post("/reset-password")
def reset_password(data: ResetPassword, db=Depends(get_db)):
    """Consume a reset token once and revoke all earlier credentials atomically."""
    payload = decode_token(data.token, "reset")
    result = db.execute(
        update(User)
        .where(
            User.id == int(payload["sub"]),
            User.token_version == payload["version"],
            User.verified.is_(True),
        )
        .values(
            password_hash=password_hash.hash(data.password),
            token_version=User.token_version + 1,
        )
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(401, "Invalid or already used reset token")
    db.commit()
    try:
        services.invalidate_user(payload["sub"])
    except RedisError as error:
        raise HTTPException(503, "Authorization cache unavailable") from error
    return {"message": "Password changed; sign in again"}
