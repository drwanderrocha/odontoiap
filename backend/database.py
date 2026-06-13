"""
OdontoAI — Database Layer v2.0
SQLite async (aiosqlite) com schema completo baseado no PRD.

Mudanças v1 → v2:
- Tabela 'profissionais' (dentistas/equipe)
- Tabela 'pacientes' expandida (endereço, estado civil, etc.)
- Tabela 'anamneses' (questionários de saúde)
- Tabela 'odontogramas' (JSON com todos os dentes)
- Tabela 'prontuarios' (fichas clínicas completas)
- Tabela 'orcamentos' (orçamentos por paciente)
- Tabela 'financeiro' (receitas/despesas)
- Tabela 'documentos' (uploads: fotos, rx, etc.)
- Tabela 'conversas' (histórico chat IA)
- Tabela 'alertas_retorno' (follow-up automático)
- Tabela 'configuracoes' (settings)
- Tabela 'auditoria' (logs LGPD)
- Tabela 'sessoes' (tokens JWT)
- Views úteis
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


# ==================== SCHEMA v2 ====================

SCHEMA_SQL = """
-- ============================================================
-- 1. PROFISSIONAIS
-- ============================================================
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

-- ============================================================
-- 2. PACIENTES (expandido)
-- ============================================================
CREATE TABLE IF NOT EXISTS pacientes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT NOT NULL,
    apelido         TEXT,
    data_nascimento TEXT,
    sexo            TEXT CHECK(sexo IN ('M', 'F', 'O')),
    cpf             TEXT UNIQUE,
    rg              TEXT,
    estado_civil    TEXT CHECK(estado_civil IN (
                        'solteiro', 'casado', 'divorciado',
                        'viuvo', 'uniao_estavel', 'nao_informado'
                    )),
    escolaridade    TEXT,
    profissao       TEXT,
    email           TEXT,
    celular         TEXT,
    fone_fixo       TEXT,
    endereco        TEXT,
    como_conheceu   TEXT,
    tipo_sanguineo  TEXT,
    alergias        TEXT,
    medicamentos    TEXT,
    observacoes     TEXT,
    status          TEXT DEFAULT 'ativo' CHECK(status IN ('ativo', 'inativo')),
    criado_por      INTEGER REFERENCES profissionais(id),
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_pacientes_nome ON pacientes(nome);
CREATE INDEX IF NOT EXISTS idx_pacientes_cpf ON pacientes(cpf);
CREATE INDEX IF NOT EXISTS idx_pacientes_celular ON pacientes(celular);
CREATE INDEX IF NOT EXISTS idx_pacientes_status ON pacientes(status);

-- ============================================================
-- 3. ANAMNESES
-- ============================================================
CREATE TABLE IF NOT EXISTS anamneses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    modo            TEXT DEFAULT 'profissional' CHECK(modo IN ('paciente', 'profissional')),
    respostas       TEXT NOT NULL DEFAULT '{}',
    alertas         TEXT DEFAULT '[]',
    assinatura_paciente TEXT,
    assinatura_em   TEXT,
    observacoes     TEXT,
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_anamneses_paciente ON anamneses(paciente_id);

-- ============================================================
-- 4. ODONTOGRAMAS (JSON-based, como Clinicorp)
-- ============================================================
CREATE TABLE IF NOT EXISTS odontogramas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    prontuario_id   INTEGER REFERENCES prontuarios(id),
    tipo_denticao   TEXT DEFAULT 'permanente' CHECK(tipo_denticao IN ('permanente', 'mista', 'decidua')),
    dentes          TEXT NOT NULL DEFAULT '{}',
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_odontogramas_paciente ON odontogramas(paciente_id);

-- ============================================================
-- 5. PRONTUÁRIOS (fichas clínicas completas)
-- ============================================================
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

-- ============================================================
-- 6. AGENDA
-- ============================================================
CREATE TABLE IF NOT EXISTS agenda (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    data_hora_inicio TEXT NOT NULL,
    data_hora_fim   TEXT,
    tipo            TEXT DEFAULT 'consulta' CHECK(tipo IN (
                        'consulta', 'retorno', 'procedimento',
                        'avaliacao', 'emergencia', 'limpeza'
                    )),
    status          TEXT DEFAULT 'agendado' CHECK(status IN (
                        'agendado', 'confirmado', 'cancelado',
                        'realizado', 'no_show', 'reagendado'
                    )),
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
CREATE INDEX IF NOT EXISTS idx_agenda_status ON agenda(status);

-- ============================================================
-- 7. ALERTAS DE RETORNO
-- ============================================================
CREATE TABLE IF NOT EXISTS alertas_retorno (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    prontuario_id   INTEGER REFERENCES prontuarios(id),
    data_sugerida   TEXT NOT NULL,
    periodo         TEXT,
    motivo          TEXT,
    status          TEXT DEFAULT 'pendente' CHECK(status IN (
                        'pendente', 'agendado', 'realizado', 'cancelado', 'ignorado'
                    )),
    whatsapp_enviado_em   TEXT,
    whatsapp_recebido_em  TEXT,
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_alertas_paciente ON alertas_retorno(paciente_id);
CREATE INDEX IF NOT EXISTS idx_alertas_status ON alertas_retorno(status);
CREATE INDEX IF NOT EXISTS idx_alertas_data ON alertas_retorno(data_sugerida);

-- ============================================================
-- 8. ORÇAMENTOS
-- ============================================================
CREATE TABLE IF NOT EXISTS orcamentos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    itens           TEXT NOT NULL DEFAULT '[]',
    valor_total     REAL NOT NULL,
    desconto        REAL DEFAULT 0,
    desconto_tipo   TEXT CHECK(desconto_tipo IN ('percentual', 'valor')),
    valor_final     REAL NOT NULL,
    forma_pagamento TEXT,
    parcelas        INTEGER DEFAULT 1,
    status          TEXT DEFAULT 'pendente' CHECK(status IN (
                        'pendente', 'aprovado', 'recusado', 'parcial', 'expirado'
                    )),
    aprovado_em     TEXT,
    aprovado_por    TEXT,
    validade        TEXT,
    observacoes     TEXT,
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_orcamentos_paciente ON orcamentos(paciente_id);
CREATE INDEX IF NOT EXISTS idx_orcamentos_status ON orcamentos(status);

-- ============================================================
-- 9. FINANCEIRO
-- ============================================================
CREATE TABLE IF NOT EXISTS financeiro (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER REFERENCES pacientes(id),
    prontuario_id   INTEGER REFERENCES prontuarios(id),
    orcamento_id    INTEGER REFERENCES orcamentos(id),
    tipo            TEXT NOT NULL CHECK(tipo IN ('receita', 'despesa')),
    categoria       TEXT NOT NULL,
    descricao       TEXT NOT NULL,
    valor           REAL NOT NULL,
    forma_pagamento TEXT CHECK(forma_pagamento IN (
                        'dinheiro', 'pix', 'cartao_credito', 'cartao_debito',
                        'boleto', 'transferencia', 'cheque', 'convenio'
                    )),
    parcelas        INTEGER DEFAULT 1,
    numero_parcela  INTEGER DEFAULT 1,
    data_vencimento TEXT NOT NULL,
    data_pagamento  TEXT,
    status          TEXT DEFAULT 'pendente' CHECK(status IN (
                        'pendente', 'pago', 'atrasado', 'cancelado', 'parcial'
                    )),
    conciliado      INTEGER DEFAULT 0,
    conciliado_em   TEXT,
    observacoes     TEXT,
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_financeiro_paciente ON financeiro(paciente_id);
CREATE INDEX IF NOT EXISTS idx_financeiro_tipo ON financeiro(tipo);
CREATE INDEX IF NOT EXISTS idx_financeiro_status ON financeiro(status);
CREATE INDEX IF NOT EXISTS idx_financeiro_vencimento ON financeiro(data_vencimento);

-- ============================================================
-- 10. DOCUMENTOS
-- ============================================================
CREATE TABLE IF NOT EXISTS documentos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    prontuario_id   INTEGER REFERENCES prontuarios(id),
    tipo            TEXT NOT NULL CHECK(tipo IN (
                        'foto_clinica', 'radiografia', 'tomografia',
                        'atestado', 'receita', 'termo_consentimento',
                        'orcamento_assinado', 'exame_laboratorial',
                        'documento_pessoal', 'outro'
                    )),
    nome_arquivo    TEXT NOT NULL,
    caminho         TEXT NOT NULL,
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
CREATE INDEX IF NOT EXISTS idx_documentos_tipo ON documentos(tipo);

-- ============================================================
-- 11. CONVERSAS (histórico chat IA)
-- ============================================================
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
CREATE INDEX IF NOT EXISTS idx_conversas_data ON conversas(criado_em);

-- ============================================================
-- 12. CONFIGURAÇÕES
-- ============================================================
CREATE TABLE IF NOT EXISTS configuracoes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profissional_id INTEGER REFERENCES profissionais(id),
    chave           TEXT NOT NULL,
    valor           TEXT NOT NULL,
    tipo            TEXT DEFAULT 'string' CHECK(tipo IN ('string', 'number', 'boolean', 'json')),
    UNIQUE(profissional_id, chave)
);

-- ============================================================
-- 13. AUDITORIA (LGPD)
-- ============================================================
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
CREATE INDEX IF NOT EXISTS idx_auditoria_data ON auditoria(criado_em);

-- ============================================================
-- 14. SESSÕES (tokens JWT)
-- ============================================================
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
CREATE INDEX IF NOT EXISTS idx_sessoes_profissional ON sessoes(profissional_id);

-- ============================================================
-- VIEWS ÚTEIS
-- ============================================================

CREATE VIEW IF NOT EXISTS v_pacientes_ultima_consulta AS
SELECT
    p.*,
    MAX(pr.data_consulta) AS ultima_consulta,
    COUNT(pr.id) AS total_consultas
FROM pacientes p
LEFT JOIN prontuarios pr ON pr.paciente_id = p.id
GROUP BY p.id;

CREATE VIEW IF NOT EXISTS v_agenda_hoje AS
SELECT
    a.*,
    p.nome AS paciente_nome,
    p.celular AS paciente_celular,
    pr.nome AS profissional_nome
FROM agenda a
JOIN pacientes p ON p.id = a.paciente_id
JOIN profissionais pr ON pr.id = a.profissional_id
WHERE date(a.data_hora_inicio) = date('now')
ORDER BY a.data_hora_inicio;

CREATE VIEW IF NOT EXISTS v_financeiro_mensal AS
SELECT
    strftime('%Y-%m', data_vencimento) AS mes,
    tipo,
    categoria,
    SUM(valor) AS total,
    COUNT(*) AS quantidade
FROM financeiro
WHERE status != 'cancelado'
GROUP BY strftime('%Y-%m', data_vencimento), tipo, categoria
ORDER BY mes DESC;

CREATE VIEW IF NOT EXISTS v_alertas_pendentes AS
SELECT
    ar.*,
    p.nome AS paciente_nome,
    p.celular AS paciente_celular
FROM alertas_retorno ar
JOIN pacientes p ON p.id = ar.paciente_id
WHERE ar.status = 'pendente'
ORDER BY ar.data_sugerida;
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


# ==================== PROFISSIONAIS CRUD ====================

async def listar_profissionais(ativo: bool = True) -> list[dict]:
    async with get_db() as db:
        if ativo:
            rows = await db.execute_fetchall(
                "SELECT * FROM profissionais WHERE ativo = 1 ORDER BY nome"
            )
        else:
            rows = await db.execute_fetchall(
                "SELECT * FROM profissionais ORDER BY nome"
            )
        return [row_to_dict(r) for r in rows]


async def obter_profissional(profissional_id: int) -> Optional[dict]:
    async with get_db() as db:
        row = await db.execute_fetchall(
            "SELECT * FROM profissionais WHERE id = ?", (profissional_id,)
        )
        return row_to_dict(row[0]) if row else None


async def criar_profissional(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            """INSERT INTO profissionais (nome, apelido, cro, cro_uf, cpf, email, celular, senha_hash, cargo, nivel_acesso, ativo, criado_em, atualizado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["nome"],
                data.get("apelido"),
                data.get("cro"),
                data.get("cro_uf"),
                data.get("cpf"),
                data.get("email"),
                data.get("celular"),
                data.get("senha_hash", ""),
                data.get("cargo", "dentista"),
                data.get("nivel_acesso", "basico"),
                data.get("ativo", 1),
                now,
                now,
            )
        )
        await db.commit()
        return await obter_profissional(cursor.lastrowid)


async def atualizar_profissional(profissional_id: int, data: dict) -> Optional[dict]:
    async with get_db() as db:
        existing = await db.execute_fetchall(
            "SELECT * FROM profissionais WHERE id = ?", (profissional_id,)
        )
        if not existing:
            return None
        allowed = {"nome", "apelido", "cro", "cro_uf", "cpf", "email", "celular",
                   "senha_hash", "cargo", "nivel_acesso", "ativo"}
        updates = {k: v for k, v in data.items() if k in allowed and v is not None}
        if not updates:
            return await obter_profissional(profissional_id)
        updates["atualizado_em"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [profissional_id]
        await db.execute(f"UPDATE profissionais SET {set_clause} WHERE id = ?", values)
        await db.commit()
        return await obter_profissional(profissional_id)


async def deletar_profissional(profissional_id: int) -> bool:
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM profissionais WHERE id = ?", (profissional_id,))
        await db.commit()
        return cursor.rowcount > 0


# ==================== PACIENTES CRUD (expandido) ====================

async def listar_pacientes(busca: str = "", limit: int = 100, offset: int = 0) -> list[dict]:
    async with get_db() as db:
        if busca:
            pattern = f"%{busca}%"
            rows = await db.execute_fetchall(
                """SELECT * FROM pacientes 
                   WHERE nome LIKE ? OR cpf LIKE ? OR celular LIKE ? OR email LIKE ? 
                   ORDER BY nome LIMIT ? OFFSET ?""",
                (pattern, pattern, pattern, pattern, limit, offset)
            )
        else:
            rows = await db.execute_fetchall(
                "SELECT * FROM pacientes ORDER BY nome LIMIT ? OFFSET ?",
                (limit, offset)
            )
        return [row_to_dict(r) for r in rows]


async def obter_paciente(paciente_id: int) -> Optional[dict]:
    async with get_db() as db:
        row = await db.execute_fetchall(
            "SELECT * FROM pacientes WHERE id = ?", (paciente_id,)
        )
        return row_to_dict(row[0]) if row else None


async def criar_paciente(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            """INSERT INTO pacientes 
               (nome, apelido, data_nascimento, sexo, cpf, rg, estado_civil,
                escolaridade, profissao, email, celular, fone_fixo, endereco,
                como_conheceu, tipo_sanguineo, alergias, medicamentos, observacoes,
                status, criado_por, criado_em, atualizado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["nome"],
                data.get("apelido"),
                data.get("data_nascimento"),
                data.get("sexo"),
                data.get("cpf"),
                data.get("rg"),
                data.get("estado_civil"),
                data.get("escolaridade"),
                data.get("profissao"),
                data.get("email"),
                data.get("celular"),
                data.get("fone_fixo"),
                json.dumps(data.get("endereco", {})) if isinstance(data.get("endereco"), dict) else data.get("endereco"),
                data.get("como_conheceu"),
                data.get("tipo_sanguineo"),
                data.get("alergias"),
                data.get("medicamentos"),
                data.get("observacoes"),
                data.get("status", "ativo"),
                data.get("criado_por"),
                now,
                now,
            )
        )
        await db.commit()
        return await obter_paciente(cursor.lastrowid)


async def atualizar_paciente(paciente_id: int, data: dict) -> Optional[dict]:
    async with get_db() as db:
        existing = await db.execute_fetchall("SELECT * FROM pacientes WHERE id = ?", (paciente_id,))
        if not existing:
            return None
        allowed = {"nome", "apelido", "data_nascimento", "sexo", "cpf", "rg",
                   "estado_civil", "escolaridade", "profissao", "email", "celular",
                   "fone_fixo", "endereco", "como_conheceu", "tipo_sanguineo",
                   "alergias", "medicamentos", "observacoes", "status"}
        updates = {k: v for k, v in data.items() if k in allowed and v is not None}
        if not updates:
            return await obter_paciente(paciente_id)
        updates["atualizado_em"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [paciente_id]
        await db.execute(f"UPDATE pacientes SET {set_clause} WHERE id = ?", values)
        await db.commit()
        return await obter_paciente(paciente_id)


async def deletar_paciente(paciente_id: int) -> bool:
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM pacientes WHERE id = ?", (paciente_id,))
        await db.commit()
        return cursor.rowcount > 0


# ==================== ANAMNESES CRUD ====================

async def listar_anamneses(paciente_id: int) -> list[dict]:
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT * FROM anamneses WHERE paciente_id = ? ORDER BY criado_em DESC",
            (paciente_id,)
        )
        return [row_to_dict(r) for r in rows]


async def obter_anamnese(anamnese_id: int) -> Optional[dict]:
    async with get_db() as db:
        row = await db.execute_fetchall("SELECT * FROM anamneses WHERE id = ?", (anamnese_id,))
        return row_to_dict(row[0]) if row else None


async def criar_anamnese(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            """INSERT INTO anamneses 
               (paciente_id, profissional_id, modo, respostas, alertas, 
                assinatura_paciente, assinatura_em, observacoes, criado_em, atualizado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["paciente_id"],
                data["profissional_id"],
                data.get("modo", "profissional"),
                json.dumps(data.get("respostas", {})),
                json.dumps(data.get("alertas", [])),
                data.get("assinatura_paciente"),
                data.get("assinatura_em"),
                data.get("observacoes"),
                now,
                now,
            )
        )
        await db.commit()
        return await obter_anamnese(cursor.lastrowid)


# ==================== ODONTOGRAMAS CRUD ====================

async def obter_odontograma(paciente_id: int) -> Optional[dict]:
    async with get_db() as db:
        row = await db.execute_fetchall(
            "SELECT * FROM odontogramas WHERE paciente_id = ? ORDER BY criado_em DESC LIMIT 1",
            (paciente_id,)
        )
        return row_to_dict(row[0]) if row else None


async def criar_odontograma(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            """INSERT INTO odontogramas 
               (paciente_id, prontuario_id, tipo_denticao, dentes, criado_em, atualizado_em)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                data["paciente_id"],
                data.get("prontuario_id"),
                data.get("tipo_denticao", "permanente"),
                json.dumps(data.get("dentes", {})),
                now,
                now,
            )
        )
        await db.commit()
        return {"id": cursor.lastrowid}


async def atualizar_odontograma(odontograma_id: int, dentes: dict) -> bool:
    async with get_db() as db:
        cursor = await db.execute(
            "UPDATE odontogramas SET dentes = ?, atualizado_em = ? WHERE id = ?",
            (json.dumps(dentes), datetime.now().isoformat(), odontograma_id)
        )
        await db.commit()
        return cursor.rowcount > 0


# ==================== PRONTUÁRIOS CRUD ====================

async def listar_prontuarios(paciente_id: int) -> list[dict]:
    async with get_db() as db:
        rows = await db.execute_fetchall(
            """SELECT pr.*, p.nome as profissional_nome 
               FROM prontuarios pr
               LEFT JOIN profissionais p ON p.id = pr.profissional_id
               WHERE pr.paciente_id = ? 
               ORDER BY pr.data_consulta DESC""",
            (paciente_id,)
        )
        return [row_to_dict(r) for r in rows]


async def obter_prontuario(prontuario_id: int) -> Optional[dict]:
    async with get_db() as db:
        row = await db.execute_fetchall(
            "SELECT * FROM prontuarios WHERE id = ?", (prontuario_id,)
        )
        return row_to_dict(row[0]) if row else None


async def criar_prontuario(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            """INSERT INTO prontuarios 
               (paciente_id, profissional_id, anamnese_id, odontograma_id,
                data_consulta, motivo_consulta, diagnostico, cid, plano_tratamento,
                procedimentos, evolucao, prescricoes, atestado, retorno_data,
                retorno_motivo, observacoes, criado_em, atualizado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["paciente_id"],
                data["profissional_id"],
                data.get("anamnese_id"),
                data.get("odontograma_id"),
                data["data_consulta"],
                data.get("motivo_consulta"),
                data.get("diagnostico"),
                data.get("cid"),
                data.get("plano_tratamento"),
                json.dumps(data.get("procedimentos", [])),
                data.get("evolucao"),
                json.dumps(data.get("prescricoes", [])),
                data.get("atestado"),
                data.get("retorno_data"),
                data.get("retorno_motivo"),
                data.get("observacoes"),
                now,
                now,
            )
        )
        await db.commit()
        return await obter_prontuario(cursor.lastrowid)


async def atualizar_prontuario(prontuario_id: int, data: dict) -> Optional[dict]:
    async with get_db() as db:
        existing = await db.execute_fetchall("SELECT * FROM prontuarios WHERE id = ?", (prontuario_id,))
        if not existing:
            return None
        allowed = {"motivo_consulta", "diagnostico", "cid", "plano_tratamento",
                   "procedimentos", "evolucao", "prescricoes", "atestado",
                   "retorno_data", "retorno_motivo", "observacoes"}
        updates = {k: v for k, v in data.items() if k in allowed and v is not None}
        if not updates:
            return await obter_prontuario(prontuario_id)
        # Serializar JSON fields
        if "procedimentos" in updates and isinstance(updates["procedimentos"], list):
            updates["procedimentos"] = json.dumps(updates["procedimentos"])
        if "prescricoes" in updates and isinstance(updates["prescricoes"], list):
            updates["prescricoes"] = json.dumps(updates["prescricoes"])
        updates["atualizado_em"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [prontuario_id]
        await db.execute(f"UPDATE prontuarios SET {set_clause} WHERE id = ?", values)
        await db.commit()
        return await obter_prontuario(prontuario_id)


# ==================== AGENDA CRUD ====================

async def listar_agenda(data: str = "", paciente_id: int = None, profissional_id: int = None,
                        limit: int = 100, offset: int = 0) -> list[dict]:
    async with get_db() as db:
        conditions = []
        params = []
        if data:
            conditions.append("date(data_hora_inicio) = ?")
            params.append(data)
        if paciente_id:
            conditions.append("paciente_id = ?")
            params.append(paciente_id)
        if profissional_id:
            conditions.append("profissional_id = ?")
            params.append(profissional_id)
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = await db.execute_fetchall(
            f"SELECT * FROM agenda {where} ORDER BY data_hora_inicio LIMIT ? OFFSET ?",
            params + [limit, offset]
        )
        return [row_to_dict(r) for r in rows]


async def obter_agendamento(agenda_id: int) -> Optional[dict]:
    async with get_db() as db:
        row = await db.execute_fetchall("SELECT * FROM agenda WHERE id = ?", (agenda_id,))
        return row_to_dict(row[0]) if row else None


async def criar_agendamento(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            """INSERT INTO agenda 
               (paciente_id, profissional_id, data_hora_inicio, data_hora_fim,
                tipo, status, observacoes, criado_em, atualizado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["paciente_id"],
                data.get("profissional_id"),
                data["data_hora_inicio"],
                data.get("data_hora_fim"),
                data.get("tipo", "consulta"),
                data.get("status", "agendado"),
                data.get("observacoes"),
                now,
                now,
            )
        )
        await db.commit()
        return await obter_agendamento(cursor.lastrowid)


async def atualizar_agendamento(agenda_id: int, data: dict) -> Optional[dict]:
    async with get_db() as db:
        existing = await db.execute_fetchall("SELECT * FROM agenda WHERE id = ?", (agenda_id,))
        if not existing:
            return None
        allowed = {"paciente_id", "profissional_id", "data_hora_inicio", "data_hora_fim",
                   "tipo", "status", "observacoes", "confirmacao_enviada_em",
                   "confirmacao_recebida_em", "confirmacao_metodo"}
        updates = {k: v for k, v in data.items() if k in allowed and v is not None}
        if not updates:
            return await obter_agendamento(agenda_id)
        updates["atualizado_em"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [agenda_id]
        await db.execute(f"UPDATE agenda SET {set_clause} WHERE id = ?", values)
        await db.commit()
        return await obter_agendamento(agenda_id)


async def deletar_agendamento(agenda_id: int) -> bool:
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM agenda WHERE id = ?", (agenda_id,))
        await db.commit()
        return cursor.rowcount > 0


# ==================== ORÇAMENTOS CRUD ====================

async def listar_orcamentos(paciente_id: int = None, status: str = None) -> list[dict]:
    async with get_db() as db:
        conditions = []
        params = []
        if paciente_id:
            conditions.append("paciente_id = ?")
            params.append(paciente_id)
        if status:
            conditions.append("status = ?")
            params.append(status)
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = await db.execute_fetchall(
            f"SELECT * FROM orcamentos {where} ORDER BY criado_em DESC",
            params
        )
        return [row_to_dict(r) for r in rows]


async def obter_orcamento(orcamento_id: int) -> Optional[dict]:
    async with get_db() as db:
        row = await db.execute_fetchall("SELECT * FROM orcamentos WHERE id = ?", (orcamento_id,))
        return row_to_dict(row[0]) if row else None


async def criar_orcamento(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            """INSERT INTO orcamentos 
               (paciente_id, profissional_id, itens, valor_total, desconto,
                desconto_tipo, valor_final, forma_pagamento, parcelas, status,
                validade, observacoes, criado_em, atualizado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["paciente_id"],
                data.get("profissional_id"),
                json.dumps(data.get("itens", [])),
                data.get("valor_total", 0),
                data.get("desconto", 0),
                data.get("desconto_tipo"),
                data.get("valor_final", 0),
                data.get("forma_pagamento"),
                data.get("parcelas", 1),
                data.get("status", "pendente"),
                data.get("validade"),
                data.get("observacoes"),
                now,
                now,
            )
        )
        await db.commit()
        return await obter_orcamento(cursor.lastrowid)


# ==================== FINANCEIRO CRUD ====================

async def listar_financeiro(paciente_id: int = None, tipo: str = None,
                            status: str = None, mes: str = None) -> list[dict]:
    async with get_db() as db:
        conditions = []
        params = []
        if paciente_id:
            conditions.append("paciente_id = ?")
            params.append(paciente_id)
        if tipo:
            conditions.append("tipo = ?")
            params.append(tipo)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if mes:
            conditions.append("strftime('%Y-%m', data_vencimento) = ?")
            params.append(mes)
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = await db.execute_fetchall(
            f"SELECT * FROM financeiro {where} ORDER BY data_vencimento DESC",
            params
        )
        return [row_to_dict(r) for r in rows]


async def criar_financeiro(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            """INSERT INTO financeiro 
               (paciente_id, prontuario_id, orcamento_id, tipo, categoria,
                descricao, valor, forma_pagamento, parcelas, numero_parcela,
                data_vencimento, data_pagamento, status, observacoes, criado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.get("paciente_id"),
                data.get("prontuario_id"),
                data.get("orcamento_id"),
                data["tipo"],
                data["categoria"],
                data["descricao"],
                data["valor"],
                data.get("forma_pagamento"),
                data.get("parcelas", 1),
                data.get("numero_parcela", 1),
                data["data_vencimento"],
                data.get("data_pagamento"),
                data.get("status", "pendente"),
                data.get("observacoes"),
                now,
            )
        )
        await db.commit()
        return {"id": cursor.lastrowid}


# ==================== ALERTAS DE RETORNO ====================

async def listar_alertas_pendentes() -> list[dict]:
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT ar.*, p.nome as paciente_nome, p.celular as paciente_celular "
            "FROM alertas_retorno ar "
            "JOIN pacientes p ON p.id = ar.paciente_id "
            "WHERE ar.status = 'pendente' "
            "ORDER BY ar.data_sugerida"
        )
        return [row_to_dict(r) for r in rows]


async def criar_alerta_retorno(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        cursor = await db.execute(
            """INSERT INTO alertas_retorno 
               (paciente_id, prontuario_id, data_sugerida, periodo, motivo, status, criado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                data["paciente_id"],
                data.get("prontuario_id"),
                data["data_sugerida"],
                data.get("periodo"),
                data.get("motivo"),
                data.get("status", "pendente"),
                now,
            )
        )
        await db.commit()
        return {"id": cursor.lastrowid}


# ==================== CONVERSAS (histórico IA) ====================

async def salvar_conversa(profissional_id: int, papel: str, conteudo: str,
                          paciente_id: int = None, modelo: str = None,
                          fontes_rag: list = None) -> int:
    async with get_db() as db:
        cursor = await db.execute(
            """INSERT INTO conversas 
               (profissional_id, paciente_id, papel, conteudo, modelo, fontes_rag, criado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                profissional_id,
                paciente_id,
                papel,
                conteudo,
                modelo,
                json.dumps(fontes_rag or []),
                datetime.now().isoformat(),
            )
        )
        await db.commit()
        return cursor.lastrowid


async def listar_conversas(profissional_id: int, paciente_id: int = None,
                           limit: int = 50) -> list[dict]:
    async with get_db() as db:
        if paciente_id:
            rows = await db.execute_fetchall(
                "SELECT * FROM conversas WHERE profissional_id = ? AND paciente_id = ? "
                "ORDER BY criado_em DESC LIMIT ?",
                (profissional_id, paciente_id, limit)
            )
        else:
            rows = await db.execute_fetchall(
                "SELECT * FROM conversas WHERE profissional_id = ? "
                "ORDER BY criado_em DESC LIMIT ?",
                (profissional_id, limit)
            )
        return [row_to_dict(r) for r in rows]


# ==================== AUDITORIA ============================

async def registrar_auditoria(profissional_id: int, acao: str, tabela: str,
                              registro_id: int = None, dados_anteriores: dict = None,
                              dados_novos: dict = None, ip: str = None,
                              user_agent: str = None):
    async with get_db() as db:
        await db.execute(
            """INSERT INTO auditoria 
               (profissional_id, acao, tabela, registro_id, dados_anteriores,
                dados_novos, ip, user_agent, criado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                profissional_id,
                acao,
                tabela,
                registro_id,
                json.dumps(dados_anteriores) if dados_anteriores else None,
                json.dumps(dados_novos) if dados_novos else None,
                ip,
                user_agent,
                datetime.now().isoformat(),
            )
        )
        await db.commit()


# ==================== CONFIGURAÇÕES ============================

async def obter_configuracao(profissional_id: int, chave: str) -> Optional[str]:
    async with get_db() as db:
        row = await db.execute_fetchall(
            "SELECT valor FROM configuracoes WHERE profissional_id = ? AND chave = ?",
            (profissional_id, chave)
        )
        return row[0]["valor"] if row else None


async def salvar_configuracao(profissional_id: int, chave: str, valor: str,
                              tipo: str = "string"):
    async with get_db() as db:
        await db.execute(
            """INSERT OR REPLACE INTO configuracoes 
               (profissional_id, chave, valor, tipo)
               VALUES (?, ?, ?, ?)""",
            (profissional_id, chave, valor, tipo)
        )
        await db.commit()
