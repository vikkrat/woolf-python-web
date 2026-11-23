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


class Signup(BaseModel):
    """Registration fields; clients cannot assign roles or verification."""

    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOutput(BaseModel):
    """Safe account fields without password hashes."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    verified: bool
    role: str
    avatar: str | None


class EmailRequest(BaseModel):
    """Email address for verification and password reset requests."""

    email: EmailStr


class ResetPassword(BaseModel):
    """Single-use reset credential and replacement password."""

    token: str
    password: str = Field(min_length=8, max_length=128)


class TokenOutput(BaseModel):
    """OAuth2 bearer token response."""

    access_token: str
    token_type: str = "bearer"
