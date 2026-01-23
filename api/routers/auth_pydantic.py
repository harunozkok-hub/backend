
from pydantic import BaseModel, EmailStr, field_validator, StringConstraints
import re
from typing import Annotated, Optional, Literal
from datetime import datetime



class RegisterFirstRequest(BaseModel):
    company_name: Annotated[str, StringConstraints(min_length=5, max_length=100)]
    email: EmailStr
    first_name: Annotated[str, StringConstraints(min_length=2, max_length=100)]
    last_name: Annotated[str, StringConstraints(min_length=2, max_length=100)]
    password: Annotated[str, StringConstraints(min_length=8, max_length=30)]
    newsletter: Optional[bool] = False
    accept_terms: bool


    @field_validator("password")
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

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return value.strip().title()

    @field_validator("company_name", mode="before")
    @classmethod
    def clean_company(cls, value: str) -> str:
        return value.strip()
    
class ResendConfirmationRequest(BaseModel):
    email: EmailStr


class RegisterWithInviteRequest(BaseModel):
    invite_code: Annotated[str, StringConstraints(min_length=10)]
    email: EmailStr
    first_name: Annotated[str, StringConstraints(min_length=2, max_length=100)]
    last_name: Annotated[str, StringConstraints(min_length=2, max_length=100)]
    password: Annotated[str, StringConstraints(min_length=8, max_length=128)]
    newsletter: Optional[bool] = False
    accept_terms: bool



    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[A-z]", value):
            raise ValueError("Password must contain a lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain a number")
        if not re.search(r"[#?!@$%^_&*\-]", value):
            raise ValueError("Password must contain a special character")
        return value

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return value.strip().title()

class CreateInviteRequest(BaseModel):
    email: Optional[EmailStr] = None  # if provided, only that email can use it
    role: Literal["admin", "user"] = "user"  # recommend not allowing guest for now
    expires_at: Optional[datetime] = None

class CreateInviteResponse(BaseModel):
    invite_code: str