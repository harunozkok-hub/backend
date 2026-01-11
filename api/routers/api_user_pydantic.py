from pydantic import BaseModel, field_validator, StringConstraints, EmailStr
import re
from typing import Annotated, Optional
from datetime import datetime

PasswordStr = Annotated[str, StringConstraints(min_length=8)]


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

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    newsletter: bool
    role: str
    company_id: int
    is_active: bool

    model_config = {"from_attributes": True}

class RefreshTokenResponse(BaseModel):
    id: int
    user_id: int
    jti: str
    used: bool
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
