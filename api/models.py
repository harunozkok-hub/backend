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
from sqlalchemy.orm import relationship, mapped_column, Mapped
from datetime import datetime, timezone
from typing import Optional

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    users: Mapped[list["APIUser"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        single_parent=True,
    )

    wix_installation: Mapped[Optional["WixInstallation"]] = relationship(
        back_populates="company",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )

    invites: Mapped[list["CompanyInvite"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        single_parent=True,
    )


class WixInstallation(Base):
    __tablename__ = "wix_installations"

    id: Mapped[int] = mapped_column(primary_key=True)
    instance_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    site_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    company: Mapped["Company"] = relationship(back_populates="wix_installation", uselist=False)


class APIUser(Base):
    __tablename__ = "api_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    newsletter: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)

    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verification_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company: Mapped["Company"] = relationship(back_populates="users")

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        single_parent=True,
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("api_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user: Mapped["APIUser"] = relationship(back_populates="refresh_tokens")


class CompanyInvite(Base):
    __tablename__ = "company_invites"

    id: Mapped[int] = mapped_column(primary_key=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company: Mapped["Company"] = relationship(back_populates="invites")

    code: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)

    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)

    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

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
