from fastapi import Response
from dependencies.deps import HTTP_ONLY_COOKIE_SECURE

def clear_cookie(response: Response, key: str):
    response.delete_cookie(key, path="/")
    response.set_cookie(
        key=key,
        value="",
        max_age=0,
        expires=0,
        httponly=True,
        secure=HTTP_ONLY_COOKIE_SECURE,
        samesite="Lax",
        path="/",
    )