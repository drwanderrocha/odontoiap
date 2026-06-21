"""
OdontoAI — Supabase Client v2
Usa supabase-py com publishable key.
Fallback para SQLite quando Supabase não está disponível.
"""
import json
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Carregar configuração
CONFIG_PATH = Path("/opt/data/.odontoiap_config.json")
SUPABASE_KEYS_PATH = Path("/opt/data/.supabase_keys.json")


def _load_config() -> dict:
    # Prioridade: arquivo de config > variáveis de ambiente
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    if SUPABASE_KEYS_PATH.exists():
        with open(SUPABASE_KEYS_PATH) as f:
            return {"supabase": json.load(f)}
    return {}


_config = _load_config()
_supabase_cfg = _config.get("supabase", {})

SUPABASE_URL = _supabase_cfg.get("url", os.environ.get("SUPABASE_URL", ""))
SUPABASE_KEY = _supabase_cfg.get("publishable_key", os.environ.get("SUPABASE_PUBLISHABLE_KEY", ""))

# Cliente singleton
_sb = None


def get_client():
    """Retorna cliente Supabase singleton."""
    global _sb
    if _sb is None:
        try:
            from supabase import create_client
            _sb = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Supabase client created")
        except ImportError:
            logger.warning("supabase-py not installed")
            return None
        except Exception as e:
            logger.error(f"Supabase client error: {e}")
            return None
    return _sb


def is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def is_connected() -> bool:
    """Testa conexão com Supabase."""
    sb = get_client()
    if sb is None:
        return False
    try:
        # Tentar select simples
        sb.table("profissionais").select("id").limit(1).execute()
        return True
    except Exception as e:
        logger.warning(f"Supabase connection test failed: {e}")
        return False


# ==================== CRUD Helpers ====================

def select(table: str, columns: str = "*", filters: dict = None,
           order: str = None, limit: int = None) -> list:
    """SELECT no Supabase."""
    sb = get_client()
    if sb is None:
        return []
    try:
        query = sb.table(table).select(columns)
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        if order:
            query = query.order(order)
        if limit:
            query = query.limit(limit)
        result = query.execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Supabase select error: {e}")
        return []


def insert(table: str, data: dict) -> Optional[dict]:
    """INSERT no Supabase."""
    sb = get_client()
    if sb is None:
        return None
    try:
        result = sb.table(table).insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Supabase insert error: {e}")
        return None


def update(table: str, filters: str, data: dict) -> Optional[dict]:
    """UPDATE no Supabase."""
    sb = get_client()
    if sb is None:
        return None
    try:
        result = sb.table(table).update(data).eq(filters, data.get(filters)).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Supabase update error: {e}")
        return None


def delete(table: str, filters: dict) -> bool:
    """DELETE no Supabase."""
    sb = get_client()
    if sb is None:
        return False
    try:
        sb.table(table).delete().match(filters).execute()
        return True
    except Exception as e:
        logger.error(f"Supabase delete error: {e}")
        return False


def upsert(table: str, data: dict) -> Optional[dict]:
    """UPSERT no Supabase."""
    sb = get_client()
    if sb is None:
        return None
    try:
        result = sb.table(table).upsert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Supabase upsert error: {e}")
        return None
