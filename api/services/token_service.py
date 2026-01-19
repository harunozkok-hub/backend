from jose import jwt, JWTError
from fastapi import HTTPException
from datetime import timedelta, timezone, datetime
from uuid import uuid4
from typing import Optional

from models import RefreshToken, APIUser
from settings import get_settings

settings = get_settings()
SECRET_KEY = settings.AUTH_SECRET_KEY
ALGORITM = settings.AUTH_ALGORITM


def create_token(
    email: str,
    user_id: int,
    user_role: str,
    expires_delta: timedelta,
    token_type: str,
    db=None,
    company_id: int | None = None,
):
    encode_dict = {"sub": email, "id": user_id, "role": user_role, "company_id": company_id,}
    expires = datetime.now(timezone.utc) + expires_delta
    encode_dict.update({"exp": expires, "type": token_type, "jti": str(uuid4())})
    encoded_jwt = jwt.encode(encode_dict, SECRET_KEY, algorithm=ALGORITM)

    # Only save jti if it's a refresh token
    if token_type == "refresh" and db:
        db.add(
            RefreshToken(
                user_id=user_id,
                jti=encode_dict.get("jti"),
                expires_at=expires,
            )
        )
        db.commit()


    return encoded_jwt


def verify_token(token: str, expected_type: str, db=None):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITM])
        email: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")
        company_id: str = payload.get("company_id")
        token_type: str = payload.get("type")
        jti: str = payload.get("jti")

        if email is None or user_id is None:
            raise HTTPException(status_code=401, detail="Couldn't validate user!")
        if token_type != expected_type:
            raise HTTPException(status_code=401, detail="Invalid token type")
        if expected_type in ("access", "refresh") and company_id is None:
            raise HTTPException(status_code=401, detail="Wrong company id")

        # Only check jti for refresh tokens
        if token_type == "refresh" and db:
            stored = db.query(RefreshToken).filter_by(jti=jti).first()
            if not stored or stored.used or stored.revoked:
                raise HTTPException(
                    status_code=401, detail="Refresh token reused or invalid"
                )

            # Invalidate the refresh token to prevent reuse
            stored.used = True
            db.add(stored)
            db.commit()


        return {"email": email, "id": user_id, "role": user_role, "company_id": company_id}
    except JWTError:
        raise HTTPException(status_code=401, detail="Couldn't validate user!")
    

def revoke_refresh_token(refresh_cookie: Optional[str], db) -> bool:
    """
    Revoke the refresh token for the current device/session (cookie-based).
    Returns True if token was found and revoked.
    """
    if not refresh_cookie:
        return False

    try:
        payload = jwt.decode(refresh_cookie, SECRET_KEY, algorithms=[ALGORITM])
        jti: str = payload.get("jti")
        if not jti:
            return False
    except Exception:
        # invalid/expired token -> nothing to revoke
        return False

    token_row = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if not token_row:
        return False

    token_row.revoked = True
    db.commit()
    return True