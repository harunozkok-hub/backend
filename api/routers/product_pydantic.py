from pydantic import BaseModel
from typing import List, Optional


class ProductImageSchema(BaseModel):
    id: Optional[int]
    media_url: Optional[str]
    thumbnail_url: Optional[str]

    model_config = {"from_attributes": True}


class ProductAdditionalInfoSchema(BaseModel):
    id: Optional[int]
    title: Optional[str]
    description: Optional[str]

    model_config = {"from_attributes": True}


class CategoryBase(BaseModel):
    id: Optional[int]
    wix_id: Optional[str]
    name: Optional[str]
    description: Optional[str]

    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    id: Optional[int]
    wix_id: Optional[str]
    name: Optional[str]
    visible_in_wix: bool
    description: Optional[str]
    weight: Optional[float]
    price: Optional[float]
    discounted_type: Optional[str]
    discounted_amount: Optional[float]
    discounted_price: Optional[float]

    images: List[ProductImageSchema] = []
    additional_info_sections: List[ProductAdditionalInfoSchema] = []

    model_config = {"from_attributes": True}


class CategorySchema(CategoryBase):
    products: List[ProductBase] = []


class ProductSchema(ProductBase):
    categories: List[CategoryBase] = []
