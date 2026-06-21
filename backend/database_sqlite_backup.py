"""
OdontoAI — Database Layer v3.0
Supabase (PostgreSQL) com fallback para SQLite.
Usa service_role key para operações admin no backend.
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Tentar importar Supabase
try:
    from supabase_client import get_supabase_client, is_configured
    SUPABASE_AVAILABLE = is_configured()
except ImportError:
    SUPABASE_AVAILABLE = False

# Fallback SQLite
import aiosqlite

DB_DIR = Path(__file__).parent.parent / "db"
DB_PATH = DB_DIR / "odontoiap.db"

# Flag: usar Supabase ou SQLite
USE_SUPABASE = SUPABASE_AVAILABLE and os.environ.get("USE_SUPABASE", "true").lower() == "true"

logger.info(f"Database mode: {'Supabase' if USE_SUPABASE else 'SQLite'}")


# ==================== CONNECTION ====================

def _get_supabase():
    """Retorna cliente Supabase."""
    return get_supabase_client()


async def init_db():
    """Inicializa o banco de dados."""
    if USE_SUPABASE:
        logger.info("Supabase: schema deve ser aplicado via SQL Editor do Supabase")
        logger.info("Execute o conteúdo de supabase_schema.py no SQL Editor")
        return
    else:
        # SQLite fallback
        DB_DIR.mkdir(parents=True, exist_ok=True)
        # Importar schema SQLite
        from database_sqlite import SCHEMA_SQL
        async with aiosqlite.connect(str(DB_PATH)) as db:
            db.row_factory = aiosqlite.Row
            await db.executescript(SCHEMA_SQL)
            await db.commit()
        logger.info("SQLite: schema criado")


def row_to_dict(row) -> dict:
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    if hasattr(row, '_mapping'):
        return dict(row._mapping)
    if hasattr(row, 'keys'):
        return dict(row)
    return row


# ==================== PROFISSIONAIS CRUD ====================

async def listar_profissionais(ativo: bool = True) -> list[dict]:
    if USE_SUPABASE:
        sb = _get_supabase()
        query = sb.table("profissionais").select("*").order("nome")
        if ativo:
            query = query.eq("ativo", True)
        result = query.execute()
        return result.data if result.data else []
    else:
        from database_sqlite import listar_profissionais as _list
        return await _list(ativo)


async def obter_profissional(profissional_id: str) -> Optional[dict]:
    if USE_SUPABASE:
        sb = _get_supabase()
        result = sb.table("profissionais").select("*").eq("id", profissional_id).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import obter_profissional as _get
        return await _get(profissional_id)


async def criar_profissional(data: dict) -> dict:
    if USE_SUPABASE:
        sb = _get_supabase()
        now = datetime.now().isoformat()
        row = {
            "nome": data["nome"],
            "apelido": data.get("apelido"),
            "cro": data.get("cro"),
            "cro_uf": data.get("cro_uf"),
            "cpf": data.get("cpf"),
            "email": data.get("email"),
            "celular": data.get("celular"),
            "senha_hash": data.get("senha_hash", ""),
            "cargo": data.get("cargo", "dentista"),
            "nivel_acesso": data.get("nivel_acesso", "basico"),
            "ativo": data.get("ativo", True),
            "criado_em": now,
            "atualizado_em": now,
        }
        result = sb.table("profissionais").insert(row).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import criar_profissional as _create
        return await _create(data)


async def atualizar_profissional(profissional_id: str, data: dict) -> Optional[dict]:
    if USE_SUPABASE:
        sb = _get_supabase()
        data["atualizado_em"] = datetime.now().isoformat()
        result = sb.table("profissionais").update(data).eq("id", profissional_id).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import atualizar_profissional as _update
        return await _update(profissional_id, data)


# ==================== PACIENTES CRUD ====================

async def listar_pacientes(profissional_id: str = None, busca: str = None, status: str = "ativo") -> list[dict]:
    if USE_SUPABASE:
        sb = _get_supabase()
        query = sb.table("pacientes").select("*")
        if profissional_id:
            query = query.eq("profissional_id", profissional_id)
        if status:
            query = query.eq("status", status)
        if busca:
            query = query.ilike("nome", f"%{busca}%")
        query = query.order("nome")
        result = query.execute()
        return result.data if result.data else []
    else:
        from database_sqlite import listar_pacientes as _list
        return await _list(profissional_id, busca, status)


async def obter_paciente(paciente_id: str) -> Optional[dict]:
    if USE_SUPABASE:
        sb = _get_supabase()
        result = sb.table("pacientes").select("*").eq("id", paciente_id).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import obter_paciente as _get
        return await _get(paciente_id)


async def criar_paciente(data: dict) -> dict:
    if USE_SUPABASE:
        sb = _get_supabase()
        now = datetime.now().isoformat()
        row = {**data, "criado_em": now, "atualizado_em": now}
        result = sb.table("pacientes").insert(row).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import criar_paciente as _create
        return await _create(data)


async def atualizar_paciente(paciente_id: str, data: dict) -> Optional[dict]:
    if USE_SUPABASE:
        sb = _get_supabase()
        data["atualizado_em"] = datetime.now().isoformat()
        result = sb.table("pacientes").update(data).eq("id", paciente_id).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import atualizar_paciente as _update
        return await _update(paciente_id, data)


# ==================== PRONTUÁRIOS CRUD ====================

async def listar_prontuarios(paciente_id: str = None, profissional_id: str = None) -> list[dict]:
    if USE_SUPABASE:
        sb = _get_supabase()
        query = sb.table("prontuarios").select("*")
        if paciente_id:
            query = query.eq("paciente_id", paciente_id)
        if profissional_id:
            query = query.eq("profissional_id", profissional_id)
        query = query.order("data_consulta", desc=True)
        result = query.execute()
        return result.data if result.data else []
    else:
        from database_sqlite import listar_prontuarios as _list
        return await _list(paciente_id, profissional_id)


async def obter_prontuario(prontuario_id: str) -> Optional[dict]:
    if USE_SUPABASE:
        sb = _get_supabase()
        result = sb.table("prontuarios").select("*").eq("id", prontuario_id).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import obter_prontuario as _get
        return await _get(prontuario_id)


async def criar_prontuario(data: dict) -> dict:
    if USE_SUPABASE:
        sb = _get_supabase()
        now = datetime.now().isoformat()
        row = {**data, "criado_em": now, "atualizado_em": now}
        result = sb.table("prontuarios").insert(row).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import criar_prontuario as _create
        return await _create(data)


# ==================== ANAMNESES CRUD ====================

async def listar_anamneses(paciente_id: str) -> list[dict]:
    if USE_SUPABASE:
        sb = _get_supabase()
        result = sb.table("anamneses").select("*").eq("paciente_id", paciente_id).order("criado_em", desc=True).execute()
        return result.data if result.data else []
    else:
        from database_sqlite import listar_anamneses as _list
        return await _list(paciente_id)


async def criar_anamnese(data: dict) -> dict:
    if USE_SUPABASE:
        sb = _get_supabase()
        now = datetime.now().isoformat()
        row = {**data, "criado_em": now, "atualizado_em": now}
        result = sb.table("anamneses").insert(row).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import criar_anamnese as _create
        return await _create(data)


# ==================== ODONTOGRAMAS CRUD ====================

async def obter_odontograma(paciente_id: str) -> Optional[dict]:
    if USE_SUPABASE:
        sb = _get_supabase()
        result = sb.table("odontogramas").select("*").eq("paciente_id", paciente_id).order("criado_em", desc=True).limit(1).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import obter_odontograma as _get
        return await _get(paciente_id)


async def salvar_odontograma(data: dict) -> dict:
    if USE_SUPABASE:
        sb = _get_supabase()
        now = datetime.now().isoformat()
        row = {**data, "criado_em": now, "atualizado_em": now}
        result = sb.table("odontogramas").insert(row).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import salvar_odontograma as _save
        return await _save(data)


async def atualizar_odontograma(odontograma_id: str, data: dict) -> Optional[dict]:
    if USE_SUPABASE:
        sb = _get_supabase()
        data["atualizado_em"] = datetime.now().isoformat()
        result = sb.table("odontogramas").update(data).eq("id", odontograma_id).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import atualizar_odontograma as _update
        return await _update(odontograma_id, data)


# ==================== AGENDA CRUD ====================

async def listar_agenda(profissional_id: str = None, data_inicio: str = None, data_fim: str = None) -> list[dict]:
    if USE_SUPABASE:
        sb = _get_supabase()
        query = sb.table("agenda").select("*, pacientes(nome, celulares), profissionais(nome)")
        if profissional_id:
            query = query.eq("profissional_id", profissional_id)
        if data_inicio:
            query = query.gte("data_hora_inicio", data_inicio)
        if data_fim:
            query = query.lte("data_hora_inicio", data_fim)
        query = query.order("data_hora_inicio")
        result = query.execute()
        return result.data if result.data else []
    else:
        from database_sqlite import listar_agenda as _list
        return await _list(profissional_id, data_inicio, data_fim)


async def criar_agendamento(data: dict) -> dict:
    if USE_SUPABASE:
        sb = _get_supabase()
        now = datetime.now().isoformat()
        row = {**data, "criado_em": now, "atualizado_em": now}
        result = sb.table("agenda").insert(row).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import criar_agendamento as _create
        return await _create(data)


# ==================== ORÇAMENTOS CRUD ====================

async def listar_orcamentos(paciente_id: str = None, status: str = None) -> list[dict]:
    if USE_SUPABASE:
        sb = _get_supabase()
        query = sb.table("orcamentos").select("*")
        if paciente_id:
            query = query.eq("paciente_id", paciente_id)
        if status:
            query = query.eq("status", status)
        query = query.order("criado_em", desc=True)
        result = query.execute()
        return result.data if result.data else []
    else:
        from database_sqlite import listar_orcamentos as _list
        return await _list(paciente_id, status)


async def criar_orcamento(data: dict) -> dict:
    if USE_SUPABASE:
        sb = _get_supabase()
        now = datetime.now().isoformat()
        row = {**data, "criado_em": now, "atualizado_em": now}
        result = sb.table("orcamentos").insert(row).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import criar_orcamento as _create
        return await _create(data)


# ==================== ALERTAS RETORNO CRUD ====================

async def listar_alertas(profissional_id: str = None, status: str = "pendente") -> list[dict]:
    if USE_SUPABASE:
        sb = _get_supabase()
        query = sb.table("alertas_retorno").select("*, pacientes(nome, celular)")
        if status:
            query = query.eq("status", status)
        query = query.order("data_sugerida")
        result = query.execute()
        return result.data if result.data else []
    else:
        from database_sqlite import listar_alertas as _list
        return await _list(profissional_id, status)


async def criar_alerta(data: dict) -> dict:
    if USE_SUPABASE:
        sb = _get_supabase()
        now = datetime.now().isoformat()
        row = {**data, "criado_em": now, "atualizado_em": now}
        result = sb.table("alertas_retorno").insert(row).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import criar_alerta as _create
        return await _create(data)


# ==================== FINANCEIRO CRUD ====================

async def listar_financeiro(paciente_id: str = None, tipo: str = None, mes: str = None) -> list[dict]:
    if USE_SUPABASE:
        sb = _get_supabase()
        query = sb.table("financeiro").select("*")
        if paciente_id:
            query = query.eq("paciente_id", paciente_id)
        if tipo:
            query = query.eq("tipo", tipo)
        query = query.order("data_vencimento", desc=True)
        result = query.execute()
        return result.data if result.data else []
    else:
        from database_sqlite import listar_financeiro as _list
        return await _list(paciente_id, tipo, mes)


async def criar_lancamento_financeiro(data: dict) -> dict:
    if USE_SUPABASE:
        sb = _get_supabase()
        now = datetime.now().isoformat()
        row = {**data, "criado_em": now, "atualizado_em": now}
        result = sb.table("financeiro").insert(row).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import criar_lancamento_financeiro as _create
        return await _create(data)


# ==================== CONVERSAS CRUD ====================

async def salvar_conversa(profissional_id: str, papel: str, conteudo: str,
                          paciente_id: str = None, modelo: str = None,
                          tokens_entrada: int = None, tokens_saida: int = None,
                          fontes_rag: list = None) -> dict:
    if USE_SUPABASE:
        sb = _get_supabase()
        row = {
            "profissional_id": profissional_id,
            "paciente_id": paciente_id,
            "papel": papel,
            "conteudo": conteudo,
            "modelo": modelo,
            "tokens_entrada": tokens_entrada,
            "tokens_saida": tokens_saida,
            "fontes_rag": fontes_rag or [],
        }
        result = sb.table("conversas").insert(row).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import salvar_conversa as _save
        return await _save(profissional_id, papel, conteudo, paciente_id, modelo, tokens_entrada, tokens_saida, fontes_rag)


async def listar_conversas(profissional_id: str, paciente_id: str = None, limite: int = 50) -> list[dict]:
    if USE_SUPABASE:
        sb = _get_supabase()
        query = sb.table("conversas").select("*").eq("profissional_id", profissional_id)
        if paciente_id:
            query = query.eq("paciente_id", paciente_id)
        query = query.order("criado_em", desc=True).limit(limite)
        result = query.execute()
        return result.data if result.data else []
    else:
        from database_sqlite import listar_conversas as _list
        return await _list(profissional_id, paciente_id, limite)


# ==================== DOCUMENTOS CRUD ====================

async def listar_documentos(paciente_id: str) -> list[dict]:
    if USE_SUPABASE:
        sb = _get_supabase()
        result = sb.table("documentos").select("*").eq("paciente_id", paciente_id).order("criado_em", desc=True).execute()
        return result.data if result.data else []
    else:
        from database_sqlite import listar_documentos as _list
        return await _list(paciente_id)


async def criar_documento(data: dict) -> dict:
    if USE_SUPABASE:
        sb = _get_supabase()
        now = datetime.now().isoformat()
        row = {**data, "criado_em": now}
        result = sb.table("documentos").insert(row).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import criar_documento as _create
        return await _create(data)


# ==================== CONFIGURAÇÕES ====================

async def obter_configuracao(profissional_id: str, chave: str) -> Optional[str]:
    if USE_SUPABASE:
        sb = _get_supabase()
        result = sb.table("configuracoes").select("valor").eq("profissional_id", profissional_id).eq("chave", chave).execute()
        return result.data[0]["valor"] if result.data else None
    else:
        from database_sqlite import obter_configuracao as _get
        return await _get(profissional_id, chave)


async def salvar_configuracao(profissional_id: str, chave: str, valor: str, tipo: str = "string"):
    if USE_SUPABASE:
        sb = _get_supabase()
        row = {"profissional_id": profissional_id, "chave": chave, "valor": valor, "tipo": tipo}
        result = sb.table("configuracoes").upsert(row).execute()
        return result.data[0] if result.data else None
    else:
        from database_sqlite import salvar_configuracao as _save
        return await _save(profissional_id, chave, valor, tipo)


# ==================== AUDITORIA ====================

async def registrar_auditoria(profissional_id: str, acao: str, tabela: str,
                               registro_id: str = None, dados_anteriores: dict = None,
                               dados_novos: dict = None, ip: str = None):
    if USE_SUPABASE:
        sb = _get_supabase()
        row = {
            "profissional_id": profissional_id,
            "acao": acao,
            "tabela": tabela,
            "registro_id": registro_id,
            "dados_anteriores": dados_anteriores,
            "dados_novos": dados_novos,
            "ip": ip,
        }
        try:
            sb.table("auditoria").insert(row).execute()
        except Exception as e:
            logger.error(f"Erro auditoria: {e}")
    else:
        from database_sqlite import registrar_auditoria as _reg
        await _reg(profissional_id, acao, tabela, registro_id, dados_anteriores, dados_novos, ip)
