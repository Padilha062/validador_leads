import re
from typing import List

_NON_DIGIT = re.compile(r"\D")


def sanitize_phone_number(phone: str) -> str:
    digits = _NON_DIGIT.sub("", phone.strip())

    if len(digits) < 10:
        raise ValueError(f"Número inválido (poucos dígitos): {phone!r}")

    if digits.startswith("55") and len(digits) in (12, 13):
        return digits

    if len(digits) in (10, 11):
        return f"55{digits}"

    raise ValueError(f"Número inválido para normalização: {phone!r}")


def parse_phone_list(raw_text: str) -> List[str]:
    seen: dict = {}
    for entry in re.split(r"[\n,;]+", raw_text):
        entry = entry.strip()
        if not entry:
            continue
        try:
            seen.setdefault(sanitize_phone_number(entry), None)
        except ValueError:
            continue
    return list(seen)
