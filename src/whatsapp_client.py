import httpx

from config import EVOLUTION_API_KEY, EVOLUTION_API_URL, EVOLUTION_INSTANCE_NAME

_EMPTY_PROFILE: dict = {"id": "", "name": "", "status": "", "profilePictureUrl": ""}
_PROFILE_KEYS = ("id", "name", "status", "profilePictureUrl")
_API_URL = f"{EVOLUTION_API_URL.rstrip('/')}/chat/fetchProfile/{EVOLUTION_INSTANCE_NAME}"
_HEADERS = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}


def _parse_profile(data: dict) -> dict:
    return {key: data.get(key, "") for key in _PROFILE_KEYS}


def _handle_error(exc: Exception) -> dict:
    if isinstance(exc, httpx.TimeoutException):
        return {**_EMPTY_PROFILE, "_error": "timeout"}
    if isinstance(exc, httpx.HTTPStatusError):
        return {**_EMPTY_PROFILE, "_error": f"HTTP {exc.response.status_code}"}
    return {**_EMPTY_PROFILE, "_error": str(exc)}


def fetch_profile(phone: str, client: httpx.Client) -> dict:
    try:
        response = client.post(
            _API_URL,
            headers=_HEADERS,
            json={"number": phone},
            timeout=20.0,
        )
        response.raise_for_status()
        return _parse_profile(response.json())
    except Exception as exc:
        return _handle_error(exc)


async def fetch_profile_async(phone: str, client: httpx.AsyncClient) -> dict:
    try:
        response = await client.post(
            _API_URL,
            headers=_HEADERS,
            json={"number": phone},
            timeout=20.0,
        )
        response.raise_for_status()
        return _parse_profile(response.json())
    except Exception as exc:
        return _handle_error(exc)
