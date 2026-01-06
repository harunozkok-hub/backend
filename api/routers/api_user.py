from fastapi import APIRouter, HTTPException
from models import APIUser, RefreshToken
from starlette import status


from routers.api_user_pydantic import UserPassVerification, UserResponse, RefreshTokenResponse
from dependencies.deps import (
    db_dependency,
    bcrypt_context,
    user_dependency,
    admin_dependency,
    company_id_dependency
)


router = APIRouter(prefix="/api-user", tags=["api-user"])


@router.get("/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    user_model = db.query(APIUser).filter(APIUser.id == user.get("id")).first()
    if not user_model:
        raise HTTPException(status_code=404, detail="User not found")

    return user_model


@router.get("/company-users",response_model=list[UserResponse], status_code=status.HTTP_200_OK)
async def get_users(admin: admin_dependency, company_id: company_id_dependency, db: db_dependency):
    # return only users in the admin's company
    return (
        db.query(APIUser)
        .filter(APIUser.company_id == company_id)
        .order_by(APIUser.id.asc())
        .all()
    )


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
    if not bcrypt_context.verify(user_password_verification.password, user_model.hashed_password):
        raise HTTPException(status_code=400, detail="Wrong password")
    
    if not user_model:
        raise HTTPException(status_code=404, detail="User not found")
    
    if bcrypt_context.verify(user_password_verification.new_password, user_model.hashed_password):
        raise HTTPException(status_code=400, detail="New password cannot be the same as old one")
    
    user_model.hashed_password = bcrypt_context.hash(
        user_password_verification.new_password
    )
    db.add(user_model)
    db.commit()
