"""
whatsapp_client.py
==================
Cliente HTTP assíncrono configurado para a Evolution API (Open-Source).
Consulta o endpoint ``/chat/fetchProfile/{instance}`` para obter metadados
do perfil de WhatsApp a partir de um número de telefone.
"""

import httpx

from config import EVOLUTION_API_KEY, EVOLUTION_API_URL, EVOLUTION_INSTANCE_NAME


# ── Dicionário padrão retornado em caso de falha ────────────────────────────
_EMPTY_PROFILE: dict = {
    "id": "",
    "name": "",
    "status": "",
    "profilePictureUrl": "",
}


async def fetch_profile_metadata(
    phone: str,
    client: httpx.AsyncClient,
) -> dict:
    """Consulta os metadados do perfil de WhatsApp para um número.

    Realiza um POST no endpoint ``/chat/fetchProfile/{instance}`` da
    Evolution API enviando o número no body JSON.

    Args:
        phone: Número de telefone já sanitizado (ex.: ``5511999999999``).
        client: Instância de ``httpx.AsyncClient`` para reutilização de
                conexões.

    Returns:
        Dicionário com as chaves ``id``, ``name``, ``status`` e
        ``profilePictureUrl``. Se a chamada falhar por qualquer motivo
        (timeout, número inválido, erro de rede), retorna o dicionário
        padrão vazio ``_EMPTY_PROFILE``.

    Examples:
        >>> import httpx, asyncio
        >>> async def demo():
        ...     async with httpx.AsyncClient() as c:
        ...         result = await fetch_profile_metadata("5511999999999", c)
        ...         print(result)
        >>> asyncio.run(demo())
    """
    url = (
        f"{EVOLUTION_API_URL.rstrip('/')}"
        f"/chat/fetchProfile/{EVOLUTION_INSTANCE_NAME}"
    )
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }
    body = {"number": phone}

    try:
        response = await client.post(
            url,
            headers=headers,
            json=body,
            timeout=20.0,
        )
        response.raise_for_status()
        data: dict = response.json()

        # Garante que as chaves esperadas existam no retorno
        return {
            "id": data.get("id", ""),
            "name": data.get("name", ""),
            "status": data.get("status", ""),
            "profilePictureUrl": data.get("profilePictureUrl", ""),
        }

    except httpx.TimeoutException:
        return {**_EMPTY_PROFILE, "_error": "Timeout na requisição"}

    except httpx.HTTPStatusError as exc:
        return {**_EMPTY_PROFILE, "_error": f"HTTP {exc.response.status_code}"}

    except Exception as exc:  # noqa: BLE001
        return {**_EMPTY_PROFILE, "_error": str(exc)}
