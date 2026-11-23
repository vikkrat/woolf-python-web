"""Validated request bodies and explicit public response shapes."""

from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ContactInput(BaseModel):
    """Complete contact representation used for creation and replacement."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    phone: str = Field(min_length=3, max_length=32, pattern=r"^\+?[0-9() .-]+$")
    birthday: date
    additional_data: str | None = Field(default=None, max_length=5000)

    @field_validator("birthday")
    @classmethod
    def birthday_not_future(cls, value):
        """Reject birth dates later than today."""
        if value > date.today():
            raise ValueError("Birthday cannot be in the future")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        """Use a consistent representation for lookup and uniqueness."""
        return str(value).lower()


class ContactOutput(ContactInput):
    """Contact response with database identifier."""

    model_config = ConfigDict(from_attributes=True)
    id: int
