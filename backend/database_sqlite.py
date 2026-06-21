"""
OdontoAI — Database Layer SQLite (fallback)
Versão original com aiosqlite para uso local quando Supabase não está configurado.
"""
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

import aiosqlite

DB_DIR = Path(__file__).parent.parent / "db"
DB_PATH = DB_DIR / "odontoiap.db"


# ==================== SCHEMA ====================

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS profissionais (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT NOT NULL,
    apelido         TEXT,
    cro             TEXT UNIQUE,
    cro_uf          TEXT,
    cpf             TEXT UNIQUE,
    email           TEXT UNIQUE,
    celular         TEXT,
    senha_hash      TEXT NOT NULL,
    cargo           TEXT DEFAULT 'dentista',
    nivel_acesso    TEXT DEFAULT 'basico',
    ativo           INTEGER DEFAULT 1,
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pacientes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profissional_id INTEGER REFERENCES profissionais(id),
    nome            TEXT NOT NULL,
    apelido         TEXT,
    data_nascimento TEXT,
    sexo            TEXT CHECK(sexo IN ('M', 'F', 'O')),
    cpf             TEXT UNIQUE,
    rg              TEXT,
    estado_civil    TEXT,
    escolaridade    TEXT,
    profissao       TEXT,
    email           TEXT,
    celular         TEXT,
    fone_fixo       TEXT,
    endereco        TEXT,
    cidade          TEXT,
    estado          TEXT,
    cep             TEXT,
    como_conheceu   TEXT,
    tipo_sanguineo  TEXT,
    alergias        TEXT,
    medicamentos    TEXT,
    observacoes     TEXT,
    status          TEXT DEFAULT 'ativo',
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_pacientes_nome ON pacientes(nome);
CREATE INDEX IF NOT EXISTS idx_pacientes_cpf ON pacientes(cpf);
CREATE INDEX IF NOT EXISTS idx_pacientes_profissional ON pacientes(profissional_id);

CREATE TABLE IF NOT EXISTS anamneses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    modo            TEXT DEFAULT 'profissional',
    respostas       TEXT NOT NULL DEFAULT '{}',
    alertas         TEXT DEFAULT '[]',
    assinatura_paciente TEXT,
    assinatura_em   TEXT,
    observacoes     TEXT,
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_anamneses_paciente ON anamneses(paciente_id);

CREATE TABLE IF NOT EXISTS odontogramas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    prontuario_id   INTEGER REFERENCES prontuarios(id),
    tipo_denticao   TEXT DEFAULT 'permanente',
    dentes          TEXT NOT NULL DEFAULT '{}',
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_odontogramas_paciente ON odontogramas(paciente_id);

CREATE TABLE IF NOT EXISTS prontuarios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    anamnese_id     INTEGER REFERENCES anamneses(id),
    odontograma_id  INTEGER REFERENCES odontogramas(id),
    data_consulta   TEXT NOT NULL,
    motivo_consulta TEXT,
    diagnostico     TEXT,
    cid             TEXT,
    plano_tratamento TEXT,
    procedimentos   TEXT DEFAULT '[]',
    evolucao        TEXT,
    prescricoes     TEXT DEFAULT '[]',
    atestado        TEXT,
    retorno_data    TEXT,
    retorno_motivo  TEXT,
    observacoes     TEXT,
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_prontuarios_paciente ON prontuarios(paciente_id);
CREATE INDEX IF NOT EXISTS idx_prontuarios_profissional ON prontuarios(profissional_id);
CREATE INDEX IF NOT EXISTS idx_prontuarios_data ON prontuarios(data_consulta);

CREATE TABLE IF NOT EXISTS agenda (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    data_hora_inicio TEXT NOT NULL,
    data_hora_fim   TEXT,
    tipo            TEXT DEFAULT 'consulta',
    status          TEXT DEFAULT 'agendado',
    confirmacao_enviada_em   TEXT,
    confirmacao_recebida_em  TEXT,
    confirmacao_metodo       TEXT,
    eh_retorno               INTEGER DEFAULT 0,
    consulta_origem_id       INTEGER,
    observacoes     TEXT,
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_agenda_paciente ON agenda(paciente_id);
CREATE INDEX IF NOT EXISTS idx_agenda_profissional ON agenda(profissional_id);
CREATE INDEX IF NOT EXISTS idx_agenda_data ON agenda(data_hora_inicio);
CREATE INDEX IF EXISTS idx_agenda_status ON agenda(status);

CREATE TABLE IF NOT EXISTS alertas_retorno (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    prontuario_id   INTEGER REFERENCES prontuarios(id),
    data_sugerida   TEXT NOT NULL,
    periodo         TEXT,
    motivo          TEXT,
    status          TEXT DEFAULT 'pendente',
    whatsapp_enviado_em   TEXT,
    whatsapp_recebido_em  TEXT,
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_alertas_paciente ON alertas_retorno(paciente_id);
CREATE INDEX IF NOT EXISTS idx_alertas_status ON alertas_retorno(status);
CREATE INDEX IF NOT EXISTS idx_alertas_data ON alertas_retorno(data_sugerida);

CREATE TABLE IF NOT EXISTS orcamentos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    itens           TEXT NOT NULL DEFAULT '[]',
    valor_total     REAL NOT NULL,
    desconto        REAL DEFAULT 0,
    desconto_tipo   TEXT,
    valor_final     REAL NOT NULL,
    forma_pagamento TEXT,
    parcelas        INTEGER DEFAULT 1,
    status          TEXT DEFAULT 'pendente',
    aprovado_em     TEXT,
    aprovado_por    TEXT,
    validade        TEXT,
    observacoes     TEXT,
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_orcamentos_paciente ON orcamentos(paciente_id);
CREATE INDEX IF NOT EXISTS idx_orcamentos_status ON orcamentos(status);

CREATE TABLE IF NOT EXISTS financeiro (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER REFERENCES pacientes(id),
    prontuario_id   INTEGER REFERENCES prontuarios(id),
    orcamento_id    INTEGER REFERENCES orcamentos(id),
    tipo            TEXT NOT NULL CHECK(tipo IN ('receita', 'despesa')),
    categoria       TEXT NOT NULL,
    descricao       TEXT NOT NULL,
    valor           REAL NOT NULL,
    forma_pagamento TEXT,
    parcelas        INTEGER DEFAULT 1,
    numero_parcela  INTEGER DEFAULT 1,
    data_vencimento TEXT NOT NULL,
    data_pagamento  TEXT,
    status          TEXT DEFAULT 'pendente',
    conciliado      INTEGER DEFAULT 0,
    conciliado_em   TEXT,
    observacoes     TEXT,
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_financeiro_paciente ON financeiro(paciente_id);
CREATE INDEX IF NOT EXISTS idx_financeiro_tipo ON financeiro(tipo);
CREATE INDEX IF NOT EXISTS idx_financeiro_status ON financeiro(status);

CREATE TABLE IF NOT EXISTS documentos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    prontuario_id   INTEGER REFERENCES prontuarios(id),
    tipo            TEXT NOT NULL,
    nome_arquivo    TEXT NOT NULL,
    storage_path    TEXT NOT NULL,
    tamanho_bytes   INTEGER,
    mime_type       TEXT,
    descricao       TEXT,
    data_documento  TEXT,
    assinado        INTEGER DEFAULT 0,
    assinatura      TEXT,
    assinado_em     TEXT,
    criado_por      INTEGER REFERENCES profissionais(id),
    criado_em       TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_documentos_paciente ON documentos(paciente_id);

CREATE TABLE IF NOT EXISTS conversas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    paciente_id     INTEGER REFERENCES pacientes(id),
    papel           TEXT NOT NULL CHECK(papel IN ('user', 'assistant', 'system')),
    conteudo        TEXT NOT NULL,
    modelo          TEXT,
    tokens_entrada  INTEGER,
    tokens_saida    INTEGER,
    fontes_rag      TEXT DEFAULT '[]',
    contexto        TEXT,
    criado_em       TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_conversas_profissional ON conversas(profissional_id);
CREATE INDEX IF NOT EXISTS idx_conversas_paciente ON conversas(paciente_id);

CREATE TABLE IF NOT EXISTS configuracoes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profissional_id INTEGER REFERENCES profissionais(id),
    chave           TEXT NOT NULL,
    valor           TEXT NOT NULL,
    tipo            TEXT DEFAULT 'string',
    UNIQUE(profissional_id, chave)
);

CREATE TABLE IF NOT EXISTS auditoria (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profissional_id INTEGER REFERENCES profissionais(id),
    acao            TEXT NOT NULL,
    tabela          TEXT NOT NULL,
    registro_id     INTEGER,
    dados_anteriores TEXT,
    dados_novos     TEXT,
    ip              TEXT,
    user_agent      TEXT,
    criado_em       TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_auditoria_profissional ON auditoria(profissional_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_tabela ON auditoria(tabela);

CREATE TABLE IF NOT EXISTS sessoes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    token           TEXT NOT NULL UNIQUE,
    expira_em       TEXT NOT NULL,
    ip              TEXT,
    user_agent      TEXT,
    ativo           INTEGER DEFAULT 1,
    criado_em       TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_sessoes_token ON sessoes(token);
"""


# ==================== CONNECTION ====================

@asynccontextmanager
async def get_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript(SCHEMA_SQL)
        await db.commit()


def row_to_dict(row) -> dict:
    if row is None:
        return None
    return dict(row)


# ==================== PROFISSIONAIS ====================

async def listar_profissionais(ativo: bool = True) -> list[dict]:
    async with get_db() as db:
        if ativo:
            rows = await db.execute_fetchall("SELECT * FROM profissionais WHERE ativo = 1 ORDER BY nome")
        else:
            rows = await db.execute_fetchall("SELECT * FROM profissionais ORDER BY nome")
        return [row_to_dict(r) for r in rows]


async def obter_profissional(profissional_id: int) -> Optional[dict]:
    async with get_db() as db:
        row = await db.execute_fetchall("SELECT * FROM profissionais WHERE id = ?", (profissional_id,))
        return row_to_dict(row[0]) if row else None


async def criar_profissional(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            """INSERT INTO profissionais (nome, apelido, cro, cro_uf, cpf, email, celular, senha_hash, cargo, nivel_acesso, ativo, criado_em, atualizado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data["nome"], data.get("apelido"), data.get("cro"), data.get("cro_uf"),
             data.get("cpf"), data.get("email"), data.get("celular"),
             data.get("senha_hash", ""), data.get("cargo", "dentista"),
             data.get("nivel_acesso", "basico"), data.get("ativo", 1), now, now)
        )
        await db.commit()
        return await obter_profissional(cursor.lastrowid)


async def atualizar_profissional(profissional_id: int, data: dict) -> Optional[dict]:
    async with get_db() as db:
        existing = await db.execute_fetchall("SELECT * FROM profissionais WHERE id = ?", (profissional_id,))
        if not existing:
            return None
        data["atualizado_em"] = datetime.now().isoformat()
        fields = ", ".join(f"{k} = ?" for k in data.keys())
        values = list(data.values()) + [profissional_id]
        await db.execute(f"UPDATE profissionais SET {fields} WHERE id = ?", values)
        await db.commit()
        return await obter_profissional(profissional_id)


# ==================== PACIENTES ====================

async def listar_pacientes(profissional_id: int = None, busca: str = None, status: str = "ativo") -> list[dict]:
    async with get_db() as db:
        query = "SELECT * FROM pacientes WHERE 1=1"
        params = []
        if profissional_id:
            query += " AND profissional_id = ?"
            params.append(profissional_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        if busca:
            query += " AND nome LIKE ?"
            params.append(f"%{busca}%")
        query += " ORDER BY nome"
        rows = await db.execute_fetchall(query, params)
        return [row_to_dict(r) for r in rows]


async def obter_paciente(paciente_id: int) -> Optional[dict]:
    async with get_db() as db:
        row = await db.execute_fetchall("SELECT * FROM pacientes WHERE id = ?", (paciente_id,))
        return row_to_dict(row[0]) if row else None


async def criar_paciente(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        data["criado_em"] = now
        data["atualizado_em"] = now
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        await db.execute(f"INSERT INTO pacientes ({cols}) VALUES ({placeholders})", list(data.values()))
        await db.commit()
        return await obter_paciente(db.execute_fetchall("SELECT lastrowid()").__await__().__iter__().__next__()[0])


async def atualizar_paciente(paciente_id: int, data: dict) -> Optional[dict]:
    async with get_db() as db:
        data["atualizado_em"] = datetime.now().isoformat()
        fields = ", ".join(f"{k} = ?" for k in data.keys())
        values = list(data.values()) + [paciente_id]
        await db.execute(f"UPDATE pacientes SET {fields} WHERE id = ?", values)
        await db.commit()
        return await obter_paciente(paciente_id)


# ==================== PRONTUÁRIOS ====================

async def listar_prontuarios(paciente_id: int = None, profissional_id: int = None) -> list[dict]:
    async with get_db() as db:
        query = "SELECT * FROM prontuarios WHERE 1=1"
        params = []
        if paciente_id:
            query += " AND paciente_id = ?"
            params.append(paciente_id)
        if profissional_id:
            query += " AND profissional_id = ?"
            params.append(profissional_id)
        query += " ORDER BY data_consulta DESC"
        rows = await db.execute_fetchall(query, params)
        return [row_to_dict(r) for r in rows]


async def obter_prontuario(prontuario_id: int) -> Optional[dict]:
    async with get_db() as db:
        row = await db.execute_fetchall("SELECT * FROM prontuarios WHERE id = ?", (prontuario_id,))
        return row_to_dict(row[0]) if row else None


async def criar_prontuario(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        data["criado_em"] = now
        data["atualizado_em"] = now
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        cursor = await db.execute(f"INSERT INTO prontuarios ({cols}) VALUES ({placeholders})", list(data.values()))
        await db.commit()
        return await obter_prontuario(cursor.lastrowid)


# ==================== ANAMNESES ====================

async def listar_anamneses(paciente_id: int) -> list[dict]:
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT * FROM anamneses WHERE paciente_id = ? ORDER BY criado_em DESC", (paciente_id,))
        return [row_to_dict(r) for r in rows]


async def criar_anamnese(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        data["criado_em"] = now
        data["atualizado_em"] = now
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        cursor = await db.execute(f"INSERT INTO anamneses ({cols}) VALUES ({placeholders})", list(data.values()))
        await db.commit()
        row = await db.execute_fetchall("SELECT * FROM anamneses WHERE id = ?", (cursor.lastrowid,))
        return row_to_dict(row[0]) if row else None


# ==================== ODONTOGRAMAS ====================

async def obter_odontograma(paciente_id: int) -> Optional[dict]:
    async with get_db() as db:
        row = await db.execute_fetchall(
            "SELECT * FROM odontogramas WHERE paciente_id = ? ORDER BY criado_em DESC LIMIT 1", (paciente_id,))
        return row_to_dict(row[0]) if row else None


async def salvar_odontograma(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        data["criado_em"] = now
        data["atualizado_em"] = now
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        cursor = await db.execute(f"INSERT INTO odontogramas ({cols}) VALUES ({placeholders})", list(data.values()))
        await db.commit()
        row = await db.execute_fetchall("SELECT * FROM odontogramas WHERE id = ?", (cursor.lastrowid,))
        return row_to_dict(row[0]) if row else None


async def atualizar_odontograma(odontograma_id: int, data: dict) -> Optional[dict]:
    async with get_db() as db:
        data["atualizado_em"] = datetime.now().isoformat()
        fields = ", ".join(f"{k} = ?" for k in data.keys())
        values = list(data.values()) + [odontograma_id]
        await db.execute(f"UPDATE odontogramas SET {fields} WHERE id = ?", values)
        await db.commit()
        row = await db.execute_fetchall("SELECT * FROM odontogramas WHERE id = ?", (odontograma_id,))
        return row_to_dict(row[0]) if row else None


# ==================== AGENDA ====================

async def listar_agenda(profissional_id: int = None, data_inicio: str = None, data_fim: str = None) -> list[dict]:
    async with get_db() as db:
        query = "SELECT * FROM agenda WHERE 1=1"
        params = []
        if profissional_id:
            query += " AND profissional_id = ?"
            params.append(profissional_id)
        if data_inicio:
            query += " AND data_hora_inicio >= ?"
            params.append(data_inicio)
        if data_fim:
            query += " AND data_hora_inicio <= ?"
            params.append(data_fim)
        query += " ORDER BY data_hora_inicio"
        rows = await db.execute_fetchall(query, params)
        return [row_to_dict(r) for r in rows]


async def criar_agendamento(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        data["criado_em"] = now
        data["atualizado_em"] = now
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        cursor = await db.execute(f"INSERT INTO agenda ({cols}) VALUES ({placeholders})", list(data.values()))
        await db.commit()
        row = await db.execute_fetchall("SELECT * FROM agenda WHERE id = ?", (cursor.lastrowid,))
        return row_to_dict(row[0]) if row else None


# ==================== ORÇAMENTOS ====================

async def listar_orcamentos(paciente_id: int = None, status: str = None) -> list[dict]:
    async with get_db() as db:
        query = "SELECT * FROM orcamentos WHERE 1=1"
        params = []
        if paciente_id:
            query += " AND paciente_id = ?"
            params.append(paciente_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY criado_em DESC"
        rows = await db.execute_fetchall(query, params)
        return [row_to_dict(r) for r in rows]


async def criar_orcamento(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        data["criado_em"] = now
        data["atualizado_em"] = now
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        cursor = await db.execute(f"INSERT INTO orcamentos ({cols}) VALUES ({placeholders})", list(data.values()))
        await db.commit()
        row = await db.execute_fetchall("SELECT * FROM orcamentos WHERE id = ?", (cursor.lastrowid,))
        return row_to_dict(row[0]) if row else None


# ==================== ALERTAS RETORNO ====================

async def listar_alertas(profissional_id: int = None, status: str = "pendente") -> list[dict]:
    async with get_db() as db:
        query = "SELECT * FROM alertas_retorno WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY data_sugerida"
        rows = await db.execute_fetchall(query, params)
        return [row_to_dict(r) for r in rows]


async def criar_alerta(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        data["criado_em"] = now
        data["atualizado_em"] = now
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        cursor = await db.execute(f"INSERT INTO alertas_retorno ({cols}) VALUES ({placeholders})", list(data.values()))
        await db.commit()
        row = await db.execute_fetchall("SELECT * FROM alertas_retorno WHERE id = ?", (cursor.lastrowid,))
        return row_to_dict(row[0]) if row else None


# ==================== FINANCEIRO ====================

async def listar_financeiro(paciente_id: int = None, tipo: str = None, mes: str = None) -> list[dict]:
    async with get_db() as db:
        query = "SELECT * FROM financeiro WHERE 1=1"
        params = []
        if paciente_id:
            query += " AND paciente_id = ?"
            params.append(paciente_id)
        if tipo:
            query += " AND tipo = ?"
            params.append(tipo)
        query += " ORDER BY data_vencimento DESC"
        rows = await db.execute_fetchall(query, params)
        return [row_to_dict(r) for r in rows]


async def criar_lancamento_financeiro(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        data["criado_em"] = now
        data["atualizado_em"] = now
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        cursor = await db.execute(f"INSERT INTO financeiro ({cols}) VALUES ({placeholders})", list(data.values()))
        await db.commit()
        row = await db.execute_fetchall("SELECT * FROM financeiro WHERE id = ?", (cursor.lastrowid,))
        return row_to_dict(row[0]) if row else None


# ==================== CONVERSAS ====================

async def salvar_conversa(profissional_id: int, papel: str, conteudo: str,
                          paciente_id: int = None, modelo: str = None,
                          tokens_entrada: int = None, tokens_saida: int = None,
                          fontes_rag: list = None) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            """INSERT INTO conversas (profissional_id, paciente_id, papel, conteudo, modelo, tokens_entrada, tokens_saida, fontes_rag, criado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (profissional_id, paciente_id, papel, conteudo, modelo, tokens_entrada, tokens_saida,
             json.dumps(fontes_rag or []), now)
        )
        await db.commit()
        row = await db.execute_fetchall("SELECT * FROM conversas WHERE id = ?", (cursor.lastrowid,))
        return row_to_dict(row[0]) if row else None


async def listar_conversas(profissional_id: int, paciente_id: int = None, limite: int = 50) -> list[dict]:
    async with get_db() as db:
        query = "SELECT * FROM conversas WHERE profissional_id = ?"
        params = [profissional_id]
        if paciente_id:
            query += " AND paciente_id = ?"
            params.append(paciente_id)
        query += " ORDER BY criado_em DESC LIMIT ?"
        params.append(limite)
        rows = await db.execute_fetchall(query, params)
        return [row_to_dict(r) for r in rows]


# ==================== DOCUMENTOS ====================

async def listar_documentos(paciente_id: int) -> list[dict]:
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT * FROM documentos WHERE paciente_id = ? ORDER BY criado_em DESC", (paciente_id,))
        return [row_to_dict(r) for r in rows]


async def criar_documento(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        data["criado_em"] = now
        cols = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        cursor = await db.execute(f"INSERT INTO documentos ({cols}) VALUES ({placeholders})", list(data.values()))
        await db.commit()
        row = await db.execute_fetchall("SELECT * FROM documentos WHERE id = ?", (cursor.lastrowid,))
        return row_to_dict(row[0]) if row else None


# ==================== CONFIGURAÇÕES ====================

async def obter_configuracao(profissional_id: int, chave: str) -> Optional[str]:
    async with get_db() as db:
        row = await db.execute_fetchall(
            "SELECT valor FROM configuracoes WHERE profissional_id = ? AND chave = ?",
            (profissional_id, chave))
        return row[0]["valor"] if row else None


async def salvar_configuracao(profissional_id: int, chave: str, valor: str, tipo: str = "string"):
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO configuracoes (profissional_id, chave, valor, tipo) VALUES (?, ?, ?, ?)",
            (profissional_id, chave, valor, tipo))
        await db.commit()
        return {"profissional_id": profissional_id, "chave": chave, "valor": valor, "tipo": tipo}


# ==================== AUDITORIA ====================

async def registrar_auditoria(profissional_id: int, acao: str, tabela: str,
                               registro_id: int = None, dados_anteriores: dict = None,
                               dados_novos: dict = None, ip: str = None):
    async with get_db() as db:
        now = datetime.now().isoformat()
        await db.execute(
            """INSERT INTO auditoria (profissional_id, acao, tabela, registro_id, dados_anteriores, dados_novos, ip, criado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (profissional_id, acao, tabela, registro_id,
             json.dumps(dados_anteriores) if dados_anteriores else None,
             json.dumps(dados_novos) if dados_novos else None, ip, now))
        await db.commit()
