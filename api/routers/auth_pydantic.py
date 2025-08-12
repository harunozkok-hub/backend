from pydantic import BaseModel, EmailStr, field_validator, StringConstraints
import re
from typing import Literal, Annotated


class CreateUserRequest(BaseModel):
    email: EmailStr
    first_name: Annotated[str, StringConstraints(min_length=2)]
    last_name: Annotated[str, StringConstraints(min_length=2)]
    password: Annotated[str, StringConstraints(min_length=8)]
    role: Literal["admin", "user", "guest"]

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
