"""
OdontoAI — Database Layer
SQLite async (aiosqlite) com schema completo e CRUD.
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
CREATE TABLE IF NOT EXISTS pacientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT UNIQUE,
    data_nascimento TEXT,
    telefone TEXT,
    email TEXT,
    convenio TEXT,
    alergias TEXT,
    medicamentos TEXT,
    observacoes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS odontograma (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    dente_numero INTEGER NOT NULL CHECK(dente_numero >= 11 AND dente_numero <= 48),
    face TEXT NOT NULL CHECK(face IN ('mesial','distal','oclusal','vestibular','lingual')),
    condicao TEXT NOT NULL DEFAULT 'sadio' CHECK(condicao IN ('sadio','carie','restaurado','ausente','implante','protese','coroa')),
    material TEXT CHECK(material IN ('resina','amalgama','cerometo')),
    observacao TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS consultas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    motivo TEXT,
    anamnese TEXT,
    exame_clinico TEXT,
    diagnostico TEXT,
    plano_tratamento TEXT,
    procedimentos TEXT,
    odontograma_snapshot TEXT,
    dentista TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agenda (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    data_hora TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('consulta','retorno','procedimento')),
    status TEXT NOT NULL DEFAULT 'agendado' CHECK(status IN ('agendado','confirmado','realizado','cancelado')),
    duracao_min INTEGER DEFAULT 30,
    observacao TEXT,
    lembrete_enviado INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_odontograma_paciente ON odontograma(paciente_id);
CREATE INDEX IF NOT EXISTS idx_consultas_paciente ON consultas(paciente_id);
CREATE INDEX IF NOT EXISTS idx_agenda_paciente ON agenda(paciente_id);
CREATE INDEX IF NOT EXISTS idx_agenda_data ON agenda(data_hora);
CREATE INDEX IF NOT EXISTS idx_pacientes_nome ON pacientes(nome);
CREATE INDEX IF NOT EXISTS idx_pacientes_cpf ON pacientes(cpf);
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


# ==================== PACIENTES CRUD ====================

async def listar_pacientes(busca: str = "", limit: int = 100, offset: int = 0) -> list[dict]:
    async with get_db() as db:
        if busca:
            pattern = f"%{busca}%"
            rows = await db.execute_fetchall(
                "SELECT * FROM pacientes WHERE nome LIKE ? OR cpf LIKE ? OR telefone LIKE ? ORDER BY nome LIMIT ? OFFSET ?",
                (pattern, pattern, pattern, limit, offset)
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
        cursor = await db.execute_insert(
            """INSERT INTO pacientes (nome, cpf, data_nascimento, telefone, email, convenio, alergias, medicamentos, observacoes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["nome"],
                data.get("cpf"),
                data.get("data_nascimento"),
                data.get("telefone"),
                data.get("email"),
                data.get("convenio"),
                data.get("alergias"),
                data.get("medicamentos"),
                data.get("observacoes"),
                now,
                now,
            )
        )
        await db.commit()
        return await obter_paciente(cursor[0])


async def atualizar_paciente(paciente_id: int, data: dict) -> Optional[dict]:
    async with get_db() as db:
        existing = await db.execute_fetchall(
            "SELECT * FROM pacientes WHERE id = ?", (paciente_id,)
        )
        if not existing:
            return None

        allowed = {"nome", "cpf", "data_nascimento", "telefone", "email", "convenio", "alergias", "medicamentos", "observacoes"}
        updates = {k: v for k, v in data.items() if k in allowed and v is not None}
        if not updates:
            return await obter_paciente(paciente_id)

        updates["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [paciente_id]
        await db.execute_update(
            f"UPDATE pacientes SET {set_clause} WHERE id = ?", values
        )
        await db.commit()
        return await obter_paciente(paciente_id)


async def deletar_paciente(paciente_id: int) -> bool:
    async with get_db() as db:
        cursor = await db.execute_update(
            "DELETE FROM pacientes WHERE id = ?", (paciente_id,)
        )
        await db.commit()
        return cursor > 0


# ==================== AGENDA CRUD ====================

async def listar_agenda(data: str = "", paciente_id: int = None, limit: int = 100, offset: int = 0) -> list[dict]:
    async with get_db() as db:
        conditions = []
        params = []

        if data:
            conditions.append("date(data_hora) = ?")
            params.append(data)
        if paciente_id:
            conditions.append("paciente_id = ?")
            params.append(paciente_id)

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        rows = await db.execute_fetchall(
            f"SELECT * FROM agenda {where} ORDER BY data_hora LIMIT ? OFFSET ?",
            params + [limit, offset]
        )
        return [row_to_dict(r) for r in rows]


async def obter_agendamento(agenda_id: int) -> Optional[dict]:
    async with get_db() as db:
        row = await db.execute_fetchall(
            "SELECT * FROM agenda WHERE id = ?", (agenda_id,)
        )
        return row_to_dict(row[0]) if row else None


async def criar_agendamento(data: dict) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        cursor = await db.execute_insert(
            """INSERT INTO agenda (paciente_id, data_hora, tipo, status, duracao_min, observacao, lembrete_enviado, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["paciente_id"],
                data["data_hora"],
                data.get("tipo", "consulta"),
                data.get("status", "agendado"),
                data.get("duracao_min", 30),
                data.get("observacao"),
                data.get("lembrete_enviado", 0),
                now,
            )
        )
        await db.commit()
        return await obter_agendamento(cursor[0])


async def atualizar_agendamento(agenda_id: int, data: dict) -> Optional[dict]:
    async with get_db() as db:
        existing = await db.execute_fetchall(
            "SELECT * FROM agenda WHERE id = ?", (agenda_id,)
        )
        if not existing:
            return None

        allowed = {"paciente_id", "data_hora", "tipo", "status", "duracao_min", "observacao", "lembrete_enviado"}
        updates = {k: v for k, v in data.items() if k in allowed and v is not None}
        if not updates:
            return await obter_agendamento(agenda_id)

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [agenda_id]
        await db.execute_update(
            f"UPDATE agenda SET {set_clause} WHERE id = ?", values
        )
        await db.commit()
        return await obter_agendamento(agenda_id)


async def deletar_agendamento(agenda_id: int) -> bool:
    async with get_db() as db:
        cursor = await db.execute_update(
            "DELETE FROM agenda WHERE id = ?", (agenda_id,)
        )
        await db.commit()
        return cursor > 0
