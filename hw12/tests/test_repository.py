"""Repository unit tests independent of HTTP routes."""

from datetime import date

from app import repository
from app.schemas import ContactInput


def test_repository_lifecycle(db, user, contact_data):
    data = ContactInput(**contact_data)
    saved = repository.create_contact(db, data, user.id)
    assert repository.get_contact(db, saved.id, user.id) is saved
    assert repository.get_contact(db, saved.id, user.id + 1) is None
    assert repository.list_contacts(db, user.id, query="koval") == []
    assert repository.list_contacts(db, user.id, query="olena") == [saved]
    assert repository.list_contacts(db, user.id, query="%") == []
    assert repository.list_contacts(db, user.id, skip=1) == []
    updated = repository.update_contact(
        db, saved, data.model_copy(update={"first_name": "New"})
    )
    assert updated.first_name == "New"
    repository.delete_contact(db, saved)
    assert repository.list_contacts(db, user.id) == []


def test_birthdays_year_boundary_and_leap_day(db, user, contact_data):
    for index, birthday in enumerate(
        ["2000-12-31", "2000-01-01", "2000-01-05", "2000-02-29"]
    ):
        repository.create_contact(
            db,
            ContactInput(
                **dict(contact_data, birthday=birthday, email=f"c{index}@example.com")
            ),
            user.id,
        )
    found = repository.list_contacts(
        db, user.id, birthday_days=7, today=date(2025, 12, 29)
    )
    assert {item.birthday.strftime("%m-%d") for item in found} == {"12-31", "01-01"}
    assert (
        len(
            repository.list_contacts(
                db, user.id, birthday_days=7, today=date(2025, 2, 28)
            )
        )
        == 1
    )
    assert (
        repository.list_contacts(db, user.id, birthday_days=1, today=date(2024, 2, 28))
        == []
    )
    assert (
        len(
            repository.list_contacts(
                db, user.id, birthday_days=1, today=date(2024, 2, 29)
            )
        )
        == 1
    )
