from datetime import datetime
from typing import Annotated

from email_validator import validate_email
from pydantic import BaseModel, Field, StringConstraints, field_validator


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=1024)


class RegisterRequest(BaseModel):
    email: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, to_lower=True, min_length=3, max_length=254
        ),
    ]
    display_name: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=120,
            pattern=r"^[^\x00-\x1f\x7f]+$",
        ),
    ]
    password: str = Field(min_length=15, max_length=1024)

    @field_validator("email")
    @classmethod
    def validate_address(cls, email: str) -> str:
        validate_email(email, check_deliverability=False)
        return email


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=256)


class TokenPairResponse(BaseModel):
    access_token: str
    access_expires_at: datetime
    refresh_token: str
    refresh_expires_at: datetime
