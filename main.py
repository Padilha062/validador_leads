import asyncio

import httpx

from src.data_handler import iter_phone_numbers, load_mock_leads, normalize_phone
from src.matcher import calculate_match_score
from src.whatsapp_client import fetch_profile_metadata


async def evaluate_lead(lead: dict, client: httpx.AsyncClient, semaphore: asyncio.Semaphore) -> dict:
    """Consulta todos os números de um lead e escolhe o melhor candidato."""
    async def bounded_fetch(phone: str) -> dict:
        async with semaphore:
            return await fetch_profile_metadata(phone, client)

    results = await asyncio.gather(*(bounded_fetch(phone) for phone in iter_phone_numbers(lead)))

    scored = []
    for phone, profile_data in zip(iter_phone_numbers(lead), results):
        score = calculate_match_score(lead.get("lead_name", ""), profile_data)
        scored.append({"phone": normalize_phone(phone), "score": score, "profile_data": profile_data})

    winner = max(scored, key=lambda item: item["score"]) if scored else None
    return {"lead": lead, "winner": winner, "candidates": scored}


async def main_async() -> None:
    """Ponto de entrada assíncrono do sistema."""
    leads = load_mock_leads()
    semaphore = asyncio.Semaphore(10)

    async with httpx.AsyncClient() as client:
        evaluations = await asyncio.gather(*(evaluate_lead(lead, client, semaphore) for lead in leads))

    for evaluation in evaluations:
        lead = evaluation["lead"]
        winner = evaluation["winner"]

        if winner is None:
            print(f"{lead['lead_name']}: nenhum número foi validado.")
            continue

        print(
            f"Lead {lead['lead_name']} -> vencedor: {winner['phone']} "
            f"(score {winner['score']:.2f}, perfil={winner['profile_data'].get('profile_name', '-')})"
        )


if __name__ == "__main__":
    asyncio.run(main_async())
