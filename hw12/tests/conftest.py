"""Isolated database, cache and external-provider fixtures."""

import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-only-secret-that-is-at-least-32-characters"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import services
from app.database import get_db
from app.main import app
from app.models import Base, User
from app.security import make_token, password_hash


class MemoryCache:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def setex(self, key, ttl, value):
        self.values[key] = value

    def delete(self, key):
        self.values.pop(key, None)

    def eval(self, script, count, key):
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    engine.dispose()


@pytest.fixture
def mail(monkeypatch):
    sent = []
    monkeypatch.setattr(services, "send_email", lambda *args: sent.append(args))
    return sent


@pytest.fixture
def client(db, monkeypatch, mail):
    monkeypatch.setattr(services, "cache", MemoryCache())
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def user(db):
    account = User(
        username="alice",
        email="alice@example.com",
        password_hash=password_hash.hash("Password123!"),
        verified=True,
        role="user",
        token_version=0,
    )
    db.add(account)
    db.commit()
    return account


@pytest.fixture
def headers(user):
    return {"Authorization": f"Bearer {make_token(user)}"}


@pytest.fixture
def contact_data():
    return {
        "first_name": "Олена",
        "last_name": "Коваль",
        "email": "olena@example.com",
        "phone": "+380501234567",
        "birthday": "2000-01-01",
        "additional_data": "friend",
    }
