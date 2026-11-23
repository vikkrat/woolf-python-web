"""Route integration tests: validation, ownership, conflicts and CRUD."""

from datetime import date, timedelta

import pytest

from app.models import User
from app.security import make_token


def test_crud_search_and_conflict(client, headers, contact_data):
    response = client.post("/contacts", json=contact_data, headers=headers)
    assert response.status_code == 201
    identifier = response.json()["id"]
    assert (
        client.get(f"/contacts/{identifier}", headers=headers).json()["first_name"]
        == "Олена"
    )
    assert (
        client.post("/contacts", json=contact_data, headers=headers).status_code == 409
    )
    assert len(client.get("/contacts?q=olena", headers=headers).json()) == 1
    assert client.get("/contacts?q=absent", headers=headers).json() == []
    changed = dict(contact_data, first_name="Марія")
    assert (
        client.put(f"/contacts/{identifier}", json=changed, headers=headers).json()[
            "first_name"
        ]
        == "Марія"
    )
    second = client.post(
        "/contacts",
        json=dict(contact_data, email="second@example.com"),
        headers=headers,
    ).json()
    assert (
        client.put(
            f"/contacts/{second['id']}", json=contact_data, headers=headers
        ).status_code
        == 409
    )
    assert client.delete(f"/contacts/{identifier}", headers=headers).status_code == 204
    assert client.get(f"/contacts/{identifier}", headers=headers).status_code == 404


def test_ownership(client, db, user, headers, contact_data):
    identifier = client.post("/contacts", json=contact_data, headers=headers).json()[
        "id"
    ]
    other = User(
        username="bob",
        email="bob@example.com",
        password_hash=user.password_hash,
        verified=True,
    )
    db.add(other)
    db.commit()
    outsider = {"Authorization": f"Bearer {make_token(other)}"}
    assert client.get("/contacts", headers=outsider).json() == []
    assert client.get(f"/contacts/{identifier}", headers=outsider).status_code == 404
    assert (
        client.put(
            f"/contacts/{identifier}", headers=outsider, json=contact_data
        ).status_code
        == 404
    )
    assert client.delete(f"/contacts/{identifier}", headers=outsider).status_code == 404
    assert (
        client.post("/contacts", json=contact_data, headers=outsider).status_code == 201
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("email", "bad"),
        ("phone", "abc"),
        ("first_name", ""),
        ("birthday", str(date.today() + timedelta(days=1))),
    ],
)
def test_validation(client, headers, contact_data, field, value):
    assert (
        client.post(
            "/contacts", json=dict(contact_data, **{field: value}), headers=headers
        ).status_code
        == 422
    )


def test_birthdays_and_unauthorized(client, headers, contact_data):
    assert client.get("/contacts").status_code == 401
    today = date.today()
    birthday = today.replace(year=2000)
    client.post(
        "/contacts", json=dict(contact_data, birthday=str(birthday)), headers=headers
    )
    assert len(client.get("/contacts/birthdays", headers=headers).json()) == 1
    assert client.get("/contacts?limit=101", headers=headers).status_code == 422
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/openapi.json").status_code == 200


def test_cors(client):
    response = client.options(
        "/contacts",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
