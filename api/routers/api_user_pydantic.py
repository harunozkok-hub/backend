from pydantic import BaseModel, field_validator, StringConstraints, EmailStr
import re
from typing import Annotated
from datetime import datetime
from models import UserRole

PasswordStr = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class CompanyUpdate(BaseModel):
    display_name: Annotated[
        str | None, StringConstraints(min_length=2, max_length=255)
    ] = None
    legal_name: Annotated[
        str | None, StringConstraints(min_length=2, max_length=255)
    ] = None
    vat_number: Annotated[
        str | None, StringConstraints(min_length=5, max_length=100)
    ] = None
    billing_email: EmailStr | None = None
    phone: str | None = None

    @field_validator("display_name", "legal_name", mode="before")
    @classmethod
    def clean_company_names(cls, value):
        if value is None:
            return None
        return str(value).strip()

    @field_validator("vat_number", mode="before")
    @classmethod
    def clean_vat(cls, value):
        if value is None:
            return None
        return str(value).strip()

    @field_validator("phone")
    @classmethod
    def normalize_company_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) > 30:
            raise ValueError("phone max length is 30")
        return v


class CompanyResponse(BaseModel):
    name: str
    slug: str
    display_name: str | None = None
    legal_name: str | None = None
    vat_number: str | None = None
    billing_email: EmailStr | None = None
    phone: str | None = None

    model_config = {"from_attributes": True}


class CompanyResponseLimited(BaseModel):
    name: str
    display_name: str | None = None
    legal_name: str | None = None

    model_config = {"from_attributes": True}


class UserPassVerification(BaseModel):
    password: PasswordStr
    new_password: PasswordStr

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:

        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain a lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain a number")
        if not re.search(r"[#?!@$%^_&*\-]", value):
            raise ValueError("Password must contain a special character")
        return value


class UserProfileUpdate(BaseModel):
    first_name: Annotated[
        str | None, StringConstraints(min_length=2, max_length=100)
    ] = None
    last_name: Annotated[
        str | None, StringConstraints(min_length=2, max_length=100)
    ] = None
    job_title: Annotated[
        str | None, StringConstraints(min_length=2, max_length=100)
    ] = None
    phone: str | None = None
    newsletter: bool | None = None

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def clean_name(cls, value: str) -> str:
        if value is None:
            return None
        return value.strip().title()

    @field_validator("job_title", mode="before")
    @classmethod
    def clean_job_title(cls, value: str) -> str:
        if value is None:
            return None
        return value.strip()

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) > 30:
            raise ValueError("phone max length is 30")
        return v


class UserResponse(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    newsletter: bool
    role: UserRole
    # ✅ computed list
    permissions: list[str] = []
    job_title: str | None = None
    phone: str | None = None
    company: CompanyResponseLimited
    email_verified: bool
    is_active: bool

    model_config = {"from_attributes": True}


class RefreshTokenResponse(BaseModel):
    id: int
    user_id: int
    jti: str
    used: bool
    revoked: bool
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
