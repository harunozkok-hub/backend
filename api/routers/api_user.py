from fastapi import APIRouter, HTTPException
from models import APIUser, RefreshToken
from starlette import status


from routers.api_user_pydantic import UserPassVerification, RefreshTokenResponse
from dependencies.deps import (
    db_dependency,
    bcrypt_context,
    user_dependency,
)


router = APIRouter(prefix="/api-user", tags=["api-user"])


@router.get("/", status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    return db.query(APIUser).filter(APIUser.id == user.get("id")).first()


@router.get("/all", status_code=status.HTTP_200_OK)
async def get_users(user: user_dependency, db: db_dependency):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Authentication failed")
    return db.query(APIUser).all()


@router.get(
    "/refresh-tokens",
    response_model=list[RefreshTokenResponse],
    status_code=status.HTTP_200_OK,
)
async def get_refresh_tokens(user: user_dependency, db: db_dependency):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Authentication failed")
    return db.query(RefreshToken).order_by(RefreshToken.created_at.desc()).all()


@router.put("/password-change", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    user: user_dependency,
    db: db_dependency,
    user_password_verification: UserPassVerification,
):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    user_model = db.query(APIUser).filter(APIUser.id == user.get("id")).first()
    if not bcrypt_context.verify(
        user_password_verification.password, user_model.hashed_password
    ):
        raise HTTPException(status_code=400, detail="Wrong password")
    if bcrypt_context.verify(
        user_password_verification.new_password, user_model.hashed_password
    ):
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as old one"
        )
    user_model.hashed_password = bcrypt_context.hash(
        user_password_verification.new_password
    )
    db.add(user_model)
    db.commit()
