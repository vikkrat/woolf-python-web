"""Basic CRUD integration against an isolated relational database."""

import os

os.environ["DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.database import get_db
from app.main import app
from app.models import Base


def test_crud():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        app.dependency_overrides[get_db] = lambda: db
        try:
            with TestClient(app) as client:
                body = {
                    "first_name": "Alice",
                    "last_name": "Doe",
                    "email": "alice@example.com",
                    "phone": "+123456",
                    "birthday": "2000-01-01",
                }
                response = client.post("/contacts", json=body)
                assert response.status_code == 201
                identifier = response.json()["id"]
                assert len(client.get("/contacts?q=alice").json()) == 1
                assert client.get(f"/contacts/{identifier}").status_code == 200
                assert (
                    client.put(
                        f"/contacts/{identifier}", json=dict(body, first_name="Bob")
                    ).json()["first_name"]
                    == "Bob"
                )
                assert client.get("/contacts/birthdays").status_code == 200
                assert client.delete(f"/contacts/{identifier}").status_code == 204
                assert client.get(f"/contacts/{identifier}").status_code == 404
        finally:
            app.dependency_overrides.clear()
    engine.dispose()
