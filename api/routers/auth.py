from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import timedelta
from starlette import status

from routers.auth_pydantic import CreateUserRequest
from dependencies.deps import (
    db_dependency,
    bcrypt_context,
    ACCESS_EXPIRE_MINUTES,
    REFRESH_EXPIRE_DAYS,
    HTTP_ONLY_COOKIE_SECURE,
    SWAGGER_ACTIVE,
)
from services.token_service import verify_token, create_token
from models import APIUser


router = APIRouter(prefix="/auth", tags=["Auth"])


def authenticate_user(email: str, password: str, db):
    user = db.query(APIUser).filter(APIUser.email == email).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    create_user_model = APIUser(
        email=create_user_request.email,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        role=create_user_request.role,
    )
    db.add(create_user_model)
    db.commit()

    return create_user_model


@router.post("/login", status_code=status.HTTP_200_OK)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency,
    response: Response = None,
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Couldn't validate user!")

    access_token = create_token(
        user.email,
        user.id,
        user.role,
        timedelta(minutes=ACCESS_EXPIRE_MINUTES),
        "access",
        None,
    )
    refresh_token = create_token(
        user.email,
        user.id,
        user.role,
        timedelta(days=REFRESH_EXPIRE_DAYS),
        "refresh",
        db=db,
    )

    # Set tokens in secure HTTP-only cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=HTTP_ONLY_COOKIE_SECURE,  # Set True in production with HTTPS
        samesite="Lax",
        max_age=ACCESS_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=HTTP_ONLY_COOKIE_SECURE,
        samesite="Lax",
        max_age=REFRESH_EXPIRE_DAYS * 86400,
        path="/",
    )
    if SWAGGER_ACTIVE:
        return {"access_token": access_token, "token_type": "bearer"}

    return {"message": "User logged in"}


# endpoint for refreshtoken renewal
@router.post("/refresh")
async def refresh_token(db: db_dependency, request: Request, response: Response):
    old_refresh_token = request.cookies.get("refresh_token")
    if not old_refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    payload = verify_token(old_refresh_token, expected_type="refresh", db=db)

    # Optionally check token ID (jti) against DB to prevent reuse
    # e.g., revoke old refresh token here

    # Create new tokens
    new_access_token = create_token(
        payload.get("email"),
        payload.get("id"),
        payload.get("role"),
        timedelta(minutes=ACCESS_EXPIRE_MINUTES),
        "access",
        None,
    )
    new_refresh_token = create_token(
        payload.get("email"),
        payload.get("id"),
        payload.get("role"),
        timedelta(days=REFRESH_EXPIRE_DAYS),
        "refresh",
        db=db,
    )
    # Set both cookies
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,
        samesite="Lax",
        max_age=ACCESS_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="Lax",
        max_age=REFRESH_EXPIRE_DAYS * 86400,
        path="/",
    )

    return {"message": "Tokens rotated"}


@router.post("/logout")
async def logout(response: Response):
    # Clear cookies
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out"}
