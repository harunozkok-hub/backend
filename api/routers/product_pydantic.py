from pydantic import BaseModel, StringConstraints, Field, model_validator
from typing import List, Optional, Annotated, Literal
from typing_extensions import Self
from datetime import datetime


class ProductImageSchema(BaseModel):
    id: int | None
    media_url: str | None
    thumbnail_url: str | None

    model_config = {"from_attributes": True}


class ProductAdditionalInfoSchema(BaseModel):
    id: int | None
    title: str | None
    description: str | None

    model_config = {"from_attributes": True}


class CategoryBase(BaseModel):
    id: int
    wix_id: str
    name: Annotated[str, StringConstraints(min_length=1, max_length=50)]
    description: Annotated[str | None, StringConstraints(max_length=600)]

    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    id: int
    wix_id: str
    name: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    visible_in_wix: bool | None
    description: Annotated[str | None, StringConstraints(max_length=8000)]
    weight: Annotated[float | None, Field(lt=999999999.99, ge=0)]
    price: Annotated[float, Field(lt=999999999.99, gt=0)]
    discounted_type: Literal["AMOUNT", "PERCENT", "NONE"]
    discounted_amount: Annotated[float | None, Field(ge=0)]
    discounted_price: Annotated[float | None, Field(gt=0)]
    created_date: datetime | None
    last_updated: datetime | None
    images: List[ProductImageSchema] = []
    additional_info_sections: List[ProductAdditionalInfoSchema] = []

    model_config = {"from_attributes": True}

    @model_validator(mode='after')
    def discount_value_check(self) -> Self:
        if self.discounted_type == "PERCENT":
            if self.discounted_amount < 0 or self.discounted_amount>100:
                raise ValueError('Enter a correct percentage for discount')
        return self


class CategorySchema(CategoryBase):
    products: List[ProductBase] = []


class ProductSchema(ProductBase):
    categories: List[CategoryBase] = []
