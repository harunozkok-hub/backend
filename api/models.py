from database import Base
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    ForeignKey,
    DateTime,
    Double,
    Table,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    jti = Column(String, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    user = relationship("APIUser", back_populates="refresh_tokens")

    class Config:
        orm_mode = True


class APIUser(Base):
    __tablename__ = "api_users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete"
    )
    is_active = Column(Boolean, default=True)
    role = Column(String)


# Product route models


class ProductAdditionalInfo(Base):
    __tablename__ = "product_additional_infos"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    title = Column(String)
    description = Column(String)

    product = relationship("Product", back_populates="additional_info_sections")


class ProductImage(Base):
    __tablename__ = "product_images"
    id = Column(Integer, primary_key=True, index=True)
    media_url = Column(String)  # path to local or S3 storage
    thumbnail_url = Column(String)  # path to local or S3 storage
    is_main_media = Column(Boolean, default=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    product = relationship("Product", back_populates="images")


ProductCategory = Table(
    "product_categories",
    Base.metadata,
    Column("product_id", ForeignKey("products.id"), primary_key=True),
    Column("category_id", ForeignKey("categories.id"), primary_key=True),
)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    wix_id = Column(String, unique=True)
    name = Column(String)
    visible_in_wix = Column(Boolean, default=True)
    description = Column(String)
    weight = Column(Double)
    price = Column(Double)
    discounted_type = Column(String)
    discounted_amount = Column(Double)
    discounted_price = Column(Double)
    additional_info_sections = relationship(
        "ProductAdditionalInfo", back_populates="product", cascade="all, delete"
    )
    images = relationship(
        "ProductImage", back_populates="product", cascade="all, delete"
    )
    categories = relationship(
        "Category", secondary="product_categories", back_populates="products"
    )


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    wix_id = Column(String, unique=True)
    name = Column(String)
    visible_in_wix = Column(Boolean, default=True)
    description = Column(String)
    products = relationship(
        "Product", secondary="product_categories", back_populates="categories"
    )
