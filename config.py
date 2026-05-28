"""
config.py
=========
Carrega as variáveis de ambiente do arquivo .env e as expõe como constantes
globais para uso em todo o projeto.
"""

import os

from dotenv import load_dotenv

# Carrega variáveis do .env na raiz do projeto
load_dotenv()

# ── Constantes da Evolution API ──────────────────────────────────────────────
EVOLUTION_API_URL: str = os.getenv("EVOLUTION_API_URL", "")
EVOLUTION_API_KEY: str = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE_NAME: str = os.getenv("EVOLUTION_INSTANCE_NAME", "")
