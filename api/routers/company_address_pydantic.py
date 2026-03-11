from pydantic import BaseModel, field_validator, StringConstraints
from typing import Literal, Annotated, Optional
from datetime import datetime

CompanyAddressType = Literal["hq", "billing"]

class CompanyAddressUpsert(BaseModel):
    name: Annotated[str | None, StringConstraints(min_length=2, max_length=255)] = None
    line1: Annotated[str, StringConstraints(min_length=2, max_length=255)]
    line2: Annotated[str | None, StringConstraints(min_length=2, max_length=255)] = None
    city: Annotated[str, StringConstraints(min_length=2, max_length=120)]
    region: Annotated[str | None, StringConstraints(min_length=2, max_length=120)] = None
    postal_code: Annotated[str, StringConstraints(min_length=2, max_length=30)]
    country_code: str
    phone: Annotated[str | None, StringConstraints(min_length=2, max_length=30)] = None

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) != 2:
            raise ValueError("country_code must be 2-letter ISO code (e.g. IT)")
        return v


class CompanyAddressResponse(CompanyAddressUpsert):
    id: int
    company_id: int
    type: CompanyAddressType
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class CompanyAddressesResponse(BaseModel):
    hq: Optional[CompanyAddressResponse] = None
    billing: Optional[CompanyAddressResponse] = None
