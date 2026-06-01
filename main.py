import asyncio
import sys

import httpx

from src.phone import parse_phone_list
from src.matcher import calculate_match_score
from src.whatsapp_client import fetch_profile_async


async def _evaluate_lead(
    lead_name: str,
    phones: list[str],
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
) -> dict:
    async def bounded_fetch(phone: str) -> dict:
        async with semaphore:
            return await fetch_profile_async(phone, client)

    profiles = await asyncio.gather(*(bounded_fetch(p) for p in phones))

    candidates = [
        {
            "phone": phone,
            "score": calculate_match_score(lead_name, profile),
            "profile": profile,
        }
        for phone, profile in zip(phones, profiles)
    ]
    winner = max(candidates, key=lambda c: c["score"]) if candidates else None
    return {"lead_name": lead_name, "winner": winner, "candidates": candidates}


async def _run() -> None:
    if len(sys.argv) < 3:
        print('Uso: python main.py "<nome do lead>" "<números separados por vírgula>"')
        sys.exit(1)

    phones = parse_phone_list(sys.argv[2])
    if not phones:
        print("Nenhum número válido encontrado.")
        sys.exit(1)

    lead_name = sys.argv[1]
    async with httpx.AsyncClient() as client:
        result = await _evaluate_lead(lead_name, phones, client, asyncio.Semaphore(10))

    winner = result["winner"]
    if winner:
        print(
            f"Lead: {lead_name} → {winner['phone']} "
            f"(score {winner['score']:.2f}, perfil: {winner['profile'].get('name', '—')})"
        )
    else:
        print(f"{lead_name}: nenhum número validado.")

    print("\nCandidatos:")
    for c in result["candidates"]:
        print(f"  {c['phone']} → score: {c['score']:.2f}")


if __name__ == "__main__":
    asyncio.run(_run())
