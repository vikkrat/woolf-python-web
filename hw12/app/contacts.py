"""Authenticated contact CRUD and search endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.exc import IntegrityError

from app import repository
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas import ContactInput, ContactOutput

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=list[ContactOutput])
def listing(
    q: str | None = Query(None, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    """List or search the caller's contacts by name or email."""
    return repository.list_contacts(db, user.id, q, skip, limit)


@router.get("/birthdays", response_model=list[ContactOutput])
def birthdays(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    """Return birthdays from today through six days from today."""
    return repository.list_contacts(
        db, user.id, skip=skip, limit=limit, birthday_days=7
    )


def owned_contact(db, contact_id, owner_id):
    """Resolve an owned contact, masking other users' resources as missing."""
    contact = repository.get_contact(db, contact_id, owner_id)
    if contact is None:
        raise HTTPException(404, "Contact not found")
    return contact


@router.post("", response_model=ContactOutput, status_code=201)
def create(data: ContactInput, db=Depends(get_db), user=Depends(get_current_user)):
    """Create a contact and report duplicate email addresses as conflicts."""
    try:
        return repository.create_contact(db, data, user.id)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(409, "Contact email already exists") from error


@router.get("/{contact_id}", response_model=ContactOutput)
def retrieve(contact_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    """Get an owned contact by identifier."""
    return owned_contact(db, contact_id, user.id)


@router.put("/{contact_id}", response_model=ContactOutput)
def update(
    contact_id: int,
    data: ContactInput,
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    """Replace an owned contact."""
    contact = owned_contact(db, contact_id, user.id)
    try:
        return repository.update_contact(db, contact, data)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(409, "Contact email already exists") from error


@router.delete("/{contact_id}", status_code=204)
def remove(contact_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    """Delete an owned contact and return an empty response."""
    repository.delete_contact(db, owned_contact(db, contact_id, user.id))
    return Response(status_code=204)
