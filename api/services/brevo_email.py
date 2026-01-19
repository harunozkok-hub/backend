import httpx
from typing import Any, Optional
from dependencies.deps import BREVO_SENDER_EMAIL, BREVO_SENDER_NAME, BREVO_API_KEY, BREVO_API_URL 




class BrevoEmailError(Exception):
    pass

async def send_brevo_template_email(
    to_email: str,
    to_name: Optional[str],
    template_id: int,
    params: dict[str, Any],
) -> dict[str, Any]:

    payload: dict[str, Any] = {
        "sender": {
            "email": BREVO_SENDER_EMAIL,
            "name": BREVO_SENDER_NAME,
        },
        "to": [
            {
                "email": to_email,
                **({"name": to_name} if to_name else {}),
            }
        ],
        "templateId": template_id,
        "params": params,
    }

    headers = {
        "api-key": BREVO_API_KEY,
        "accept": "application/json",
        "content-type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(BREVO_API_URL, json=payload, headers=headers)

    if resp.status_code >= 400:
        # Brevo returns useful JSON errors; expose it for debugging/logging
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text

        raise BrevoEmailError(f"Brevo send failed ({resp.status_code}): {detail}")

    return resp.json()
