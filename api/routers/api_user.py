from fastapi import APIRouter, HTTPException
from models import APIUser, RefreshToken, CompanyAddress, Company
from starlette import status

from services.permissions import get_effective_permission_modules, attach_effective_permissions_for_company_users
from routers.api_user_pydantic import UserPassVerification, UserResponse, RefreshTokenResponse, UserProfileUpdate, CompanyResponse, CompanyUpdate
from routers.company_address_pydantic import CompanyAddressResponse, CompanyAddressUpsert
from dependencies.deps import (
    db_dependency,
    bcrypt_context,
    user_dependency,
    admin_dependency,
    company_id_dependency
)


router = APIRouter(prefix="/api-user", tags=["API User"])


@router.get("/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    user_model = db.query(APIUser).filter(APIUser.id == user.get("id")).first()
    if not user_model:
        raise HTTPException(status_code=401, detail="Session invalid")
    # ✅ compute and attach
    user_model.permissions = get_effective_permission_modules(db, user_model)

    return user_model

@router.patch("/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_profile(user: user_dependency, db: db_dependency, payload: UserProfileUpdate):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")

    user_model = db.query(APIUser).filter(APIUser.id == user.get("id")).first()
    if not user_model:
        raise HTTPException(status_code=401, detail="Session invalid")

    data = payload.model_dump(exclude_unset=True)

    # Prevent editing protected fields even if someone sends them
    data.pop("email", None)
    data.pop("role", None)
    data.pop("company_id", None)
    data.pop("email_verified", None)

    for k, v in data.items():
        setattr(user_model, k, v)
    db.add(user_model)
    db.commit()
    db.refresh(user_model)
    user_model.permissions = get_effective_permission_modules(db, user_model)
    return user_model

@router.get("/company", response_model=CompanyResponse, status_code=status.HTTP_200_OK)
async def get_company(admin: admin_dependency, company_id: company_id_dependency, db: db_dependency):
    if admin is None:
        raise HTTPException(status_code=401, detail="Authentication failed")

    company_model = db.query(Company).filter(Company.id == company_id).first()
    if not company_model:
        raise HTTPException(status_code=404, detail="Company not found")

    return company_model

@router.patch("/company", response_model=CompanyResponse, status_code=status.HTTP_200_OK)
async def update_company(admin: admin_dependency, company_id: company_id_dependency, db: db_dependency, payload: CompanyUpdate):
    if admin is None:
        raise HTTPException(status_code=401, detail="Authentication failed")

    company_model = db.query(Company).filter(Company.id == company_id).first()
    if not company_model:
        raise HTTPException(status_code=404, detail="Company not found")

    data = payload.model_dump(exclude_unset=True)

    # Safety: don't allow changing immutable fields here
    data.pop("id", None)
    data.pop("slug", None)
    data.pop("name", None)

    for k, v in data.items():
        setattr(company_model, k, v)

    db.add(company_model)
    db.commit()
    db.refresh(company_model)
    return company_model

@router.get("/company-addresses", status_code=status.HTTP_200_OK)
async def get_company_addresses(admin: admin_dependency, company_id: company_id_dependency, db: db_dependency):
    if admin is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    rows = (
        db.query(CompanyAddress)
        .filter(CompanyAddress.company_id == company_id)
        .all()
    )

    out = {"hq": None, "billing": None}
    for row in rows:
        # since type is stored as string
        if row.type in out:
            out[row.type] = CompanyAddressResponse.model_validate(row)
    return out


@router.put("/company-address/{addr_type}", response_model=CompanyAddressResponse, status_code=status.HTTP_200_OK)
async def upsert_company_address(
    addr_type: str,
    payload: CompanyAddressUpsert,
    admin: admin_dependency,
    company_id: company_id_dependency,
    db: db_dependency
):
    if admin is None:
        raise HTTPException(status_code=401, detail="Authentication failed")

    if addr_type not in ("hq", "billing"):
        raise HTTPException(status_code=400, detail="Invalid address type")

    existing = (
        db.query(CompanyAddress)
        .filter(
            CompanyAddress.company_id == company_id,
            CompanyAddress.type == addr_type,
        )
        .first()
    )

    if existing:
        for k, v in payload.model_dump().items():
            setattr(existing, k, v)
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    new_addr = CompanyAddress(
        company_id=company_id,
        type=addr_type,
        **payload.model_dump(),
    )
    db.add(new_addr)
    db.commit()
    db.refresh(new_addr)
    return new_addr

@router.get("/company-users",response_model=list[UserResponse], status_code=status.HTTP_200_OK)
async def get_users(admin: admin_dependency, company_id: company_id_dependency, db: db_dependency):
    # return only users in the admin's company
    users = (
        db.query(APIUser)
        .filter(APIUser.company_id == company_id)
        .order_by(APIUser.id.asc())
        .all()
    )

    attach_effective_permissions_for_company_users(db, users)
    return users


@router.get(
    "/refresh-tokens",
    response_model=list[RefreshTokenResponse],
    status_code=status.HTTP_200_OK,
)
async def get_refresh_tokens(admin: admin_dependency, company_id: company_id_dependency, db: db_dependency):
    # IMPORTANT:
    # RefreshToken table only has user_id, so scope tokens via join to APIUser.company_id
    return (
        db.query(RefreshToken)
        .join(APIUser, APIUser.id == RefreshToken.user_id)
        .filter(APIUser.company_id == company_id)
        .order_by(RefreshToken.created_at.desc())
        .all()
    )


@router.put("/password-change", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    user: user_dependency,
    db: db_dependency,
    user_password_verification: UserPassVerification,
):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    
    user_model = db.query(APIUser).filter(APIUser.id == user.get("id")).first()
    if not user_model:
        raise HTTPException(status_code=404, detail="User not found")

    if not bcrypt_context.verify(user_password_verification.password, user_model.hashed_password):
        raise HTTPException(status_code=400, detail="Wrong password")
    
    if bcrypt_context.verify(user_password_verification.new_password, user_model.hashed_password):
        raise HTTPException(status_code=400, detail="New password cannot be the same as old one")
    
    user_model.hashed_password = bcrypt_context.hash(
        user_password_verification.new_password
    )
    db.add(user_model)
    db.commit()
