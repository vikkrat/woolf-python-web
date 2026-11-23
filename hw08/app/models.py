"""Contact persistence model."""

from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Contact(Base):
    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    phone: Mapped[str] = mapped_column(String(32))
    birthday: Mapped[date] = mapped_column(Date)
    additional_data: Mapped[str | None] = mapped_column(Text, nullable=True)
