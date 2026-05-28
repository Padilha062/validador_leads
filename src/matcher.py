"""
matcher.py
==========
Algoritmo de pontuação por inteligência fuzzy-matching.
Compara o nome do lead com os metadados retornados pelo perfil de WhatsApp
para eleger o número mais provável de ser pessoal.
"""

from thefuzz import fuzz


def _normalize(text: str) -> str:
    """Normaliza texto para comparação: lowercase e espaços unificados."""
    return " ".join(str(text).lower().split())


def calculate_match_score(lead_name: str, profile_data: dict) -> float:
    """Calcula a pontuação final de similaridade (0 a 10).

    A pontuação é composta por três critérios:

    1. **Similaridade textual (até 6 pontos):** baseada no
       ``fuzz.partial_ratio`` entre o nome do lead e o nome retornado
       no perfil do WhatsApp.
    2. **Foto de perfil (até 2 pontos):** bonus se o campo
       ``profilePictureUrl`` estiver preenchido e válido (http/https).
    3. **Bio / Status (até 2 pontos):** bonus se o campo ``status``
       não estiver vazio.

    Args:
        lead_name: Nome completo do lead informado pelo usuário.
        profile_data: Dicionário retornado por ``fetch_profile_metadata``,
                      contendo ``name``, ``profilePictureUrl`` e ``status``.

    Returns:
        Score de 0.0 a 10.0 arredondado em duas casas decimais.

    Examples:
        >>> calculate_match_score("Carlos Silva", {"name": "Carlos S.",
        ...     "profilePictureUrl": "https://img.com/foto.jpg", "status": "Olá!"})
        9.6
    """
    profile_name = str(profile_data.get("name", "")).strip()

    # ── 1. Similaridade textual (máx. 6 pontos) ─────────────────────────
    if profile_name:
        partial = fuzz.partial_ratio(
            _normalize(lead_name),
            _normalize(profile_name),
        )
        text_score = (partial / 100.0) * 6.0
    else:
        text_score = 0.0

    # ── 2. Bonus: foto de perfil (máx. 2 pontos) ────────────────────────
    picture_url = str(profile_data.get("profilePictureUrl", "")).strip()
    bonus_picture = 2.0 if picture_url.startswith(("http://", "https://")) else 0.0

    # ── 3. Bonus: bio / status (máx. 2 pontos) ──────────────────────────
    status = str(profile_data.get("status", "")).strip()
    bonus_status = 2.0 if status else 0.0

    total = text_score + bonus_picture + bonus_status
    return round(min(total, 10.0), 2)
