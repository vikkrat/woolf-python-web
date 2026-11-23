"""Explicit local administration command; never expose role assignment publicly."""

import argparse

from sqlalchemy import select

from app import services
from app.database import SessionLocal
from app.models import User


def main():
    """Promote an existing verified account and invalidate its cached role."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email")
    args = parser.parse_args()
    with SessionLocal.begin() as db:
        user = db.scalar(select(User).where(User.email == args.email.lower()))
        if not user or not user.verified:
            parser.error("A verified account is required")
        user.role = "admin"
        user.token_version += 1
    services.invalidate_user(user.id)
    print("Role updated. Sign in again to obtain a new access token.")


if __name__ == "__main__":
    main()
