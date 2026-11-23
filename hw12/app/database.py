"""SQLAlchemy engine and request-scoped sessions."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db():
    """Yield a session and close it after the request."""
    with SessionLocal() as session:
        yield session
