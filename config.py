import os

from dotenv import load_dotenv

load_dotenv()

EVOLUTION_API_URL: str = os.getenv("EVOLUTION_API_URL", "")
EVOLUTION_API_KEY: str = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE_NAME: str = os.getenv("EVOLUTION_INSTANCE_NAME", "")

_missing = [
    name
    for name, value in {
        "EVOLUTION_API_URL": EVOLUTION_API_URL,
        "EVOLUTION_API_KEY": EVOLUTION_API_KEY,
        "EVOLUTION_INSTANCE_NAME": EVOLUTION_INSTANCE_NAME,
    }.items()
    if not value
]
if _missing:
    raise RuntimeError(
        f"Variáveis de ambiente ausentes no .env: {', '.join(_missing)}"
    )
