"""
data_handler.py
===============
Funções utilitárias para limpeza e sanitização de números de telefone.
Utiliza regex para normalizar formatos diversos para o padrão internacional
brasileiro (ex.: 5511999999999).
"""

import re
from typing import List


# Remove tudo que NÃO é dígito
_NON_DIGIT = re.compile(r"\D")


def sanitize_phone_number(phone: str) -> str:
    """Sanitiza um número de telefone para o formato internacional limpo.

    Remove espaços, parênteses, traços, pontos e o sinal de '+'.
    Em seguida, garante que o número comece com '55' (código do Brasil).

    Args:
        phone: Número de telefone em qualquer formato.

    Returns:
        String contendo apenas dígitos no padrão ``55DDNNNNNNNNN``
        (13 dígitos para celular, 12 para fixo).

    Raises:
        ValueError: Se após a limpeza o número tiver menos de 10 dígitos.

    Examples:
        >>> sanitize_phone_number("(11) 98888-1111")
        '5511988881111'
        >>> sanitize_phone_number("+55 21 99999-4444")
        '5521999994444'
        >>> sanitize_phone_number("11966663333")
        '5511966663333'
    """
    digits = _NON_DIGIT.sub("", phone.strip())

    if len(digits) < 10:
        raise ValueError(f"Número inválido (poucos dígitos): {phone!r}")

    # Se já começa com 55 e tem 12 ou 13 dígitos → já está no formato correto
    if digits.startswith("55") and len(digits) in (12, 13):
        return digits

    # Se tem 10 ou 11 dígitos (sem DDI), adiciona o '55'
    if len(digits) in (10, 11):
        return f"55{digits}"

    raise ValueError(f"Número inválido para normalização: {phone!r}")


def parse_phone_list(raw_text: str) -> List[str]:
    """Processa um bloco de texto com múltiplos números de telefone.

    Aceita números separados por quebra de linha, vírgula ou ponto-e-vírgula.
    Números inválidos são silenciosamente ignorados.

    Args:
        raw_text: Texto contendo números de telefone separados por
                  ``\\n``, ``,`` ou ``;``.

    Returns:
        Lista de números sanitizados e únicos (sem duplicatas), preservando
        a ordem de aparição.

    Examples:
        >>> parse_phone_list("(11) 98888-1111\\n11 97777-2222, 11966663333")
        ['5511988881111', '5511977772222', '5511966663333']
    """
    # Divide por quebra de linha, vírgula ou ponto-e-vírgula
    raw_entries = re.split(r"[\n,;]+", raw_text)

    seen: set = set()
    sanitized: List[str] = []

    for entry in raw_entries:
        entry = entry.strip()
        if not entry:
            continue
        try:
            number = sanitize_phone_number(entry)
            if number not in seen:
                seen.add(number)
                sanitized.append(number)
        except ValueError:
            # Ignora entradas inválidas
            continue

    return sanitized
