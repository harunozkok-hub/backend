import httpx
from fastapi import HTTPException
from settings import get_settings

settings = get_settings()


WIX_API_BASE = "https://www.wixapis.com/"
WIX_API_KEY = settings.WIX_API_KEY
WIX_SITE_ID = settings.WIX_SITE_ID


HEADERS = {
    "Authorization": WIX_API_KEY,
    "wix-site-id": WIX_SITE_ID,
    "Content-Type": "application/json",
}


async def wix_get_request(endpoint: str, params: dict = None) -> dict:
    return await _wix_request("GET", endpoint, params=params)


async def wix_post_request(endpoint: str, json_data: dict = None) -> dict:
    return await _wix_request("POST", endpoint, json=json_data)


async def wix_put_request(endpoint: str, json_data: dict) -> dict:
    return await _wix_request("PUT", endpoint, json=json_data)


async def wix_patch_request(endpoint: str, json_data: dict) -> dict:
    return await _wix_request("PATCH", endpoint, json=json_data)


async def wix_delete_request(endpoint: str) -> dict:
    return await _wix_request("DELETE", endpoint)


async def _wix_request(
    method: str, endpoint: str, params: dict = None, json: dict = None
) -> dict:
    url = WIX_API_BASE + endpoint.lstrip("/")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.request(
                method,
                url,
                headers=HEADERS,
                params=params,
                json=json,
            )

        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Wix API {method} error: {response.text}",
            )

        return response.json()

    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f"Wix {method} failed: {exc}")
