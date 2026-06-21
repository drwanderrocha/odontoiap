"""
OdontoAI — Supabase Client
Cliente singleton para conexão com Supabase (PostgreSQL + Auth + Storage).
"""
import json
import os
from pathlib import Path
from typing import Optional

# Carregar configuração do Supabase
SUPABASE_CONFIG_PATH = Path("/opt/data/.supabase_keys.json")

def _load_config() -> dict:
    if SUPABASE_CONFIG_PATH.exists():
        with open(SUPABASE_CONFIG_PATH) as f:
            return json.load(f)
    # Fallback: variáveis de ambiente
    return {
        "SUPABASE_URL": os.environ.get("SUPABASE_URL", ""),
        "SUPABASE_SERVICE_ROLE_KEY": os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""),
        "SUPABASE_PUBLISHABLE_KEY": os.environ.get("SUPABASE_PUBLISHABLE_KEY", ""),
    }

_config = _load_config()
SUPABASE_URL = _config.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = _config.get("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_PUBLISHABLE_KEY = _config.get("SUPABASE_PUBLISHABLE_KEY", "")

# Cliente Supabase (lazy init)
_supabase_client = None

def get_supabase_client():
    """Retorna cliente Supabase singleton (service role — admin)."""
    global _supabase_client
    if _supabase_client is None:
        try:
            from supabase import create_client
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        except ImportError:
            raise RuntimeError("supabase-py não instalado. Execute: pip install supabase")
    return _supabase_client


def get_anon_client():
    """Retorna cliente Supabase com chave anon (para operações do frontend)."""
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)
    except ImportError:
        raise RuntimeError("supabase-py não instalado.")


def is_configured() -> bool:
    """Verifica se o Supabase está configurado."""
    return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)
