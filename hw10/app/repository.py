"""Contact queries, always scoped to the requesting account."""

from datetime import date, timedelta

from sqlalchemy import extract, or_, select

from app.models import Contact


def list_contacts(
    db, owner_id, query=None, skip=0, limit=100, birthday_days=None, today=None
):
    """Search contacts or filter upcoming birthdays, including year rollover.

    The seven-day interval includes today and the following six days.
    February 29 birthdays are observed on February 28 in non-leap years.
    """
    statement = select(Contact).where(Contact.owner_id == owner_id)
    if query:
        statement = statement.where(
            or_(
                Contact.first_name.icontains(query, autoescape=True),
                Contact.last_name.icontains(query, autoescape=True),
                Contact.email.icontains(query, autoescape=True),
            )
        )
    if birthday_days is not None:
        start = today or date.today()
        days = [start + timedelta(days=i) for i in range(birthday_days)]
        pairs = {(day.month, day.day) for day in days}
        import calendar

        if any(
            day.month == 2 and day.day == 28 and not calendar.isleap(day.year)
            for day in days
        ):
            pairs.add((2, 29))
        statement = statement.where(
            or_(
                *[
                    (extract("month", Contact.birthday) == month)
                    & (extract("day", Contact.birthday) == day)
                    for month, day in pairs
                ]
            )
        )
    return db.scalars(statement.order_by(Contact.id).offset(skip).limit(limit)).all()


def get_contact(db, contact_id, owner_id):
    """Retrieve an owned contact or return None without revealing other owners."""
    return db.scalar(
        select(Contact).where(Contact.id == contact_id, Contact.owner_id == owner_id)
    )


def create_contact(db, data, owner_id):
    """Create a contact inside the caller's transaction."""
    contact = Contact(**data.model_dump(), owner_id=owner_id)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def update_contact(db, contact, data):
    """Replace a previously authorized contact's editable fields."""
    for key, value in data.model_dump().items():
        setattr(contact, key, value)
    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(db, contact):
    """Delete a previously authorized contact."""
    db.delete(contact)
    db.commit()
