"""Persistence models for account ownership and contact details."""

from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared ORM metadata."""


class User(Base):
    """Account with a hashed password and server-controlled role."""

    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('user', 'admin')", name="valid_role"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    verified: Mapped[bool] = mapped_column(default=False)
    role: Mapped[str] = mapped_column(String(10), default="user")
    avatar: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    token_version: Mapped[int] = mapped_column(default=0)


class Contact(Base):
    """A contact belonging to exactly one user."""

    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("owner_id", "email", name="uq_owner_email"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(254))
    phone: Mapped[str] = mapped_column(String(32))
    birthday: Mapped[date] = mapped_column(Date)
    additional_data: Mapped[str | None] = mapped_column(Text, nullable=True)
