"""Contact CRUD and search endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.exc import IntegrityError

from app import repository
from app.database import get_db
from app.schemas import ContactInput, ContactOutput

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=list[ContactOutput])
def listing(
    q: str | None = Query(None, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db=Depends(get_db),
):
    """List or search contacts by name or email."""
    return repository.list_contacts(db, None, q, skip, limit)


@router.get("/birthdays", response_model=list[ContactOutput])
def birthdays(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db=Depends(get_db),
):
    """Return birthdays from today through six days from today."""
    return repository.list_contacts(db, None, skip=skip, limit=limit, birthday_days=7)


def owned_contact(db, contact_id, owner_id):
    """Resolve a contact, masking other users' resources as missing."""
    contact = repository.get_contact(db, contact_id, owner_id)
    if contact is None:
        raise HTTPException(404, "Contact not found")
    return contact


@router.post("", response_model=ContactOutput, status_code=201)
def create(data: ContactInput, db=Depends(get_db)):
    """Create a contact and report duplicate email addresses as conflicts."""
    try:
        return repository.create_contact(db, data, None)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(409, "Contact email already exists") from error


@router.get("/{contact_id}", response_model=ContactOutput)
def retrieve(contact_id: int, db=Depends(get_db)):
    """Get a contact by identifier."""
    return owned_contact(db, contact_id, None)


@router.put("/{contact_id}", response_model=ContactOutput)
def update(contact_id: int, data: ContactInput, db=Depends(get_db)):
    """Replace a contact."""
    contact = owned_contact(db, contact_id, None)
    try:
        return repository.update_contact(db, contact, data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(409, "Contact email already exists") from error


@router.delete("/{contact_id}", status_code=204)
def remove(contact_id: int, db=Depends(get_db)):
    """Delete a contact and return an empty response."""
    repository.delete_contact(db, owned_contact(db, contact_id, None))
    return Response(status_code=204)
