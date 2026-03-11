import os
import httpx
from fastapi import HTTPException, status
from dependencies.deps import VATLAYER_API_KEY, VATLAYER_API_URL


async def vatlayer_validate(vat_number: str) -> dict:
    access_key = VATLAYER_API_KEY
    if not access_key:
        # Treat missing key as server misconfig (not user error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="VAT validation service is not configured",
        )

    params = {"access_key": VATLAYER_API_KEY, "vat_number": vat_number}

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(f"{VATLAYER_API_URL}/validate", params=params)
            r.raise_for_status()
            data = r.json()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VAT validation service timed out",
        )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VAT validation service error",
        )

    # VATlayer errors can come back as {"success": false, "error": {...}} :contentReference[oaicite:2]{index=2}
    if data.get("success") is False:
        err = data.get("error") or {}
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"VAT validation failed: {err.get('type') or 'unknown_error'}",
        )
    print(data)
    return data
