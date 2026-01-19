import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import timedelta, datetime, timezone
from starlette import status
from sqlalchemy.exc import IntegrityError

from routers.auth_pydantic import (
    CreateInviteRequest, 
    CreateInviteResponse, 
    RegisterFirstRequest, 
    RegisterWithInviteRequest)
from dependencies.deps import (
    db_dependency,
    admin_dependency,
    bcrypt_context,
    ACCESS_EXPIRE_MINUTES,
    REFRESH_EXPIRE_DAYS,
    HTTP_ONLY_COOKIE_SECURE,
    SWAGGER_ACTIVE,
)
from helpers.email import send_confirmation_mail
from services.token_service import verify_token, create_token, revoke_refresh_token
from models import APIUser, Company, CompanyInvite


router = APIRouter(prefix="/auth", tags=["Auth"])


def authenticate_user(email: str, password: str, db):
    email = email.lower().strip()
    user = db.query(APIUser).filter(APIUser.email == email).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def company_slugify(name: str) -> str:
    # simple slug: lower + trim + replace spaces with '-'
    return "-".join(name.strip().lower().split())


@router.post("/register-company", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, req: RegisterFirstRequest):
    email = req.email.lower().strip()
    company_name = req.company_name.strip()
    company_slug = company_slugify(company_name)

    # 1) email must be unique
    if db.query(APIUser).filter(APIUser.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2) company must be unique
    if db.query(Company).filter(Company.slug == company_slug).first():
        raise HTTPException(status_code=400, detail="Company already exists")
    # enforce accept terms (optional but recommended)
    if not req.accept_terms:
        raise HTTPException(status_code=400, detail="Please accept terms & conditions")


    # Create company + admin user in one transaction
    try:
        company = Company(name=company_name, slug=company_slug)
        db.add(company)
        db.flush()  # gives company.id

        user = APIUser(
            email=email,
            first_name=req.first_name,
            last_name=req.last_name,
            hashed_password=bcrypt_context.hash(req.password),
            role="admin",
            newsletter=bool(req.newsletter),
            company_id=company.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()
        # Handles race conditions (two people try same company/email at same time)
        raise HTTPException(status_code=409, detail="Email or company already exists")

    try:
        await send_confirmation_mail(
            email= user.email,
            user_id= user.id,
            user_role= user.role,
            first_name=user.first_name,
            last_name =user.last_name,
            company_name = company.name
        )
        email_sent=True
    except Exception as e:
        email_sent=False
        pass

    return {
        "email_sent": email_sent,
        "id": user.id,
        "email": user.email,
        "role": user.role
    }

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_with_invite(db: db_dependency, req: RegisterWithInviteRequest):
    email = req.email.lower().strip()

    # invite lookup
    invite = db.query(CompanyInvite).filter(CompanyInvite.code == req.invite_code).first()
    if not invite or invite.is_used:
        raise HTTPException(status_code=400, detail="Invalid invite code")

    if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invite expired")

    if invite.email and invite.email.lower().strip() != email:
        raise HTTPException(status_code=400, detail="Invite is for a different email")

    # email uniqueness
    if db.query(APIUser).filter(APIUser.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
        # enforce accept terms (optional but recommended)
    if not req.accept_terms:
        raise HTTPException(status_code=400, detail="Please accept terms & conditions")


    user = APIUser(
        email=email,
        first_name=req.first_name,
        last_name=req.last_name,
        newsletter=bool(req.newsletter),
        hashed_password=bcrypt_context.hash(req.password),
        role=invite.role or "user",
        company_id=invite.company_id,
    )
    db.add(user)

    invite.is_used = True
    db.add(invite)

    db.commit()
    db.refresh(user)

    return {"id": user.id, "email": user.email, "role": user.role, "company_id": user.company_id, "newsletter": user.newsletter,}

@router.post("/invite", response_model=CreateInviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invite(
    admin: admin_dependency,
    db: db_dependency,
    body: CreateInviteRequest,
):
    # admin includes company_id from your token
    company_id = admin.get("company_id")

    # optional: prevent issuing admin invites unless you want that
    if body.role == "admin":
        # You can allow it, but many apps restrict it.
        # If you want to allow only owner admins, keep it for later.
        pass

    # basic expires validation
    if body.expires_at and body.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="expires_at must be in the future")

    code = secrets.token_urlsafe(24)

    invite = CompanyInvite(
        company_id=company_id,
        code=code,
        email=body.email.lower().strip() if body.email else None,
        role=body.role,
        expires_at=body.expires_at,
        is_used=False,
    )
    db.add(invite)
    db.commit()

    return {"invite_code": code}

@router.get("/confirm-email", status_code=status.HTTP_200_OK)
def confirm_email(token: str, db: db_dependency):
    payload = verify_token(token, expected_type="email_confirm")
    user_id = payload.get("id")

    user = db.query(APIUser).filter(APIUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.email_verified:
        raise HTTPException(
            status_code=409, detail="Email was already verified"
        )

    user.email_verified = True
    db.commit()
    return {"message": "Email confirmed"}

@router.post("/login", status_code=status.HTTP_200_OK)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency,
    response: Response,
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Couldn't validate user!")
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in!")

    access_token = create_token(
        user.email,
        user.id,
        user.role,
        timedelta(minutes=ACCESS_EXPIRE_MINUTES),
        "access",
        None,
        company_id=user.company_id,
    )
    refresh_token = create_token(
        user.email,
        user.id,
        user.role,
        timedelta(days=REFRESH_EXPIRE_DAYS),
        "refresh",
        db=db,
        company_id=user.company_id,
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
    company_id = payload.get("company_id")

    # Create new tokens
    new_access_token = create_token(
        payload.get("email"),
        payload.get("id"),
        payload.get("role"),
        timedelta(minutes=ACCESS_EXPIRE_MINUTES),
        "access",
        None,
        company_id=company_id
    )
    new_refresh_token = create_token(
        payload.get("email"),
        payload.get("id"),
        payload.get("role"),
        timedelta(days=REFRESH_EXPIRE_DAYS),
        "refresh",
        db=db,
        company_id=company_id
    )
    # Set both cookies
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=HTTP_ONLY_COOKIE_SECURE,
        samesite="Lax",
        max_age=ACCESS_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=HTTP_ONLY_COOKIE_SECURE,
        samesite="Lax",
        max_age=REFRESH_EXPIRE_DAYS * 86400,
        path="/",
    )

    return {"message": "Tokens rotated"}


@router.post("/logout")
async def logout(response: Response, request:Request, db: db_dependency):
    available_refresh_token = request.cookies.get("refresh_token")
    revoked = revoke_refresh_token(available_refresh_token, db)
    if revoked:
        add_message = " and tokens deleted"
    else:
        add_message=""
    # Clear cookies
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": f"Logged out{add_message}"}
