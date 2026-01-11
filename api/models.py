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

class WixInstallation(Base):
    __tablename__ = "wix_installations"

    id = Column(Integer, primary_key=True, index=True)

    # The key identifier for a Wix app installation (per site installation)
    instance_id = Column(String, unique=True, index=True, nullable=False)

    # Site id is often needed for headers like "wix-site-id"
    site_id = Column(String, index=True, nullable=True)

    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )

    company_id = Column(Integer, ForeignKey("companies.id"), unique=True, nullable=False)
    company = relationship("Company", back_populates="wix_installation")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("api_users.id"), nullable=False)
    jti = Column(String, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    user = relationship("APIUser", back_populates="refresh_tokens")


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)

    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )
    users = relationship("APIUser", back_populates="company", cascade="all, delete")
    # 1 company -> 0..1 wix installation (simple version)
    wix_installation = relationship(
        "WixInstallation",
        back_populates="company",
        uselist=False,
        cascade="all, delete-orphan",
    )


class CompanyInvite(Base):
    __tablename__ = "company_invites"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    company = relationship("Company")

    code = Column(String, unique=True, index=True, nullable=False)  # store hashed if you want later
    email = Column(String, index=True, nullable=True)  # optional: bind invite to a specific email
    role = Column(String, default="user", nullable=False)

    is_used = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

class APIUser(Base):
    __tablename__ = "api_users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String)
    last_name = Column(String)
    newsletter = Column(Boolean, default=False, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user", nullable=False)

    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    company = relationship("Company", back_populates="users")
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete"
    )

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
    created_date = Column(DateTime)
    last_updated = Column(DateTime)
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
