from typing import Annotated, Optional
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

from settings import get_settings
from database import SessionLocal
from services.token_service import verify_token

settings = get_settings()

SECRET_KEY = settings.AUTH_SECRET_KEY
ALGORITM = settings.AUTH_ALGORITM
ACCESS_EXPIRE_MINUTES = settings.ACCESS_EXPIRE_MINUTES
REFRESH_EXPIRE_DAYS = settings.REFRESH_EXPIRE_DAYS
HTTP_ONLY_COOKIE_SECURE = settings.HTTP_ONLY_COOKIE_SECURE
SWAGGER_ACTIVE = settings.SWAGGER_ACTIVE


# creating db dependency to be called in db operations
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


# creating the crypting model
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# creating user dependency to get logged user before functions
oauth_bearer = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)



async def get_current_user(
    request: Request,
    db: db_dependency,
    token: Annotated[Optional[str], Security(oauth_bearer)],
):

    # If Swagger sent the token via Authorization header, use it
    if token:
        return verify_token(token, expected_type="access", db=db)

    # Otherwise fallback to cookie
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="No access token found")

    return verify_token(access_token, expected_type="access", db=db)


user_dependency = Annotated[dict, Depends(get_current_user)]



def require_company_id(user: user_dependency) -> int:
    company_id = user.get("company_id")
    if not company_id:
        raise HTTPException(status_code=401, detail="Missing company context")
    return int(company_id)


company_id_dependency = Annotated[int, Depends(require_company_id)]


def require_admin(user: user_dependency) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user


admin_dependency = Annotated[dict, Depends(require_admin)]