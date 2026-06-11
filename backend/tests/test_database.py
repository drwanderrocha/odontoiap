"""
Testes unitários para database.py
Cobertura: CRUD pacientes, CRUD agenda, schema, row_to_dict.
"""
import pytest
import pytest_asyncio
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import database as db_module


# ==================== FIXTURE GLOBAL ====================
# Usa um único banco em arquivo para todos os testes deste módulo
# (evita o problema de cada teste criar um banco diferente)

import tempfile
import shutil

_db_temp_dir = None
_db_path = None
_db_original_path = None
_db_original_dir = None


def setup_module(module):
    """Cria banco temporário uma vez para todo o módulo."""
    global _db_temp_dir, _db_path, _db_original_path, _db_original_dir
    _db_temp_dir = tempfile.mkdtemp()
    _db_path = Path(_db_temp_dir) / "test_odontoiap.db"
    _db_original_path = db_module.DB_PATH
    _db_original_dir = db_module.DB_DIR
    db_module.DB_PATH = _db_path
    db_module.DB_DIR = Path(_db_temp_dir)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(db_module.init_db())
    module._loop = loop


def teardown_module(module):
    """Limpa banco temporário."""
    global _db_temp_dir, _db_original_path, _db_original_dir
    db_module.DB_PATH = _db_original_path
    db_module.DB_DIR = _db_original_dir
    shutil.rmtree(_db_temp_dir, ignore_errors=True)
    module._loop.close()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    """Limpa tabelas antes de cada teste para isolamento."""
    async with db_module.get_db() as db:
        await db.execute("DELETE FROM agenda")
        await db.execute("DELETE FROM pacientes")
        await db.commit()
    yield


@pytest.mark.asyncio
class TestInitDb:
    """Testa inicialização do banco."""

    def test_db_path_override(self):
        assert _db_path.exists()

    def test_db_tem_tabelas(self):
        loop = asyncio.new_event_loop()

        async def check():
            async with db_module.get_db() as conn:
                cursor = await conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = [row[0] for row in await cursor.fetchall()]
                assert "pacientes" in tables
                assert "agenda" in tables
                assert "odontograma" in tables
                assert "consultas" in tables

        loop.run_until_complete(check())
        loop.close()


@pytest.mark.asyncio
class TestPacientesCRUD:
    """Testa CRUD completo de pacientes."""

    async def test_criar_paciente_completo(self):
        data = {
            "nome": "Maria da Silva",
            "cpf": "123.456.789-00",
            "data_nascimento": "1990-05-15",
            "telefone": "(11) 99999-1234",
            "email": "maria@email.com",
            "convenio": "Uniodonto",
            "alergias": "Látex",
            "medicamentos": "Losartana",
            "observacoes": "Hipertensa",
        }
        paciente = await db_module.criar_paciente(data)
        assert paciente is not None
        assert paciente["nome"] == "Maria da Silva"
        assert paciente["cpf"] == "123.456.789-00"
        assert paciente["id"] is not None
        assert paciente["created_at"] is not None

    async def test_criar_paciente_minimo(self):
        data = {"nome": "João Santos"}
        paciente = await db_module.criar_paciente(data)
        assert paciente is not None
        assert paciente["nome"] == "João Santos"
        assert paciente["id"] is not None

    async def test_obter_paciente(self):
        data = {"nome": "Ana Costa", "cpf": "987.654.321-00"}
        criado = await db_module.criar_paciente(data)
        obtido = await db_module.obter_paciente(criado["id"])
        assert obtido is not None
        assert obtido["nome"] == "Ana Costa"
        assert obtido["cpf"] == "987.654.321-00"

    async def test_obter_paciente_inexistente(self):
        resultado = await db_module.obter_paciente(99999)
        assert resultado is None

    async def test_listar_pacientes_vazio(self):
        pacientes = await db_module.listar_pacientes()
        assert pacientes == []

    async def test_listar_pacientes_com_dados(self):
        await db_module.criar_paciente({"nome": "Carlos Lima"})
        await db_module.criar_paciente({"nome": "Beatriz Souza"})
        pacientes = await db_module.listar_pacientes()
        assert len(pacientes) == 2
        # Ordenado por nome
        assert pacientes[0]["nome"] == "Beatriz Souza"
        assert pacientes[1]["nome"] == "Carlos Lima"

    async def test_buscar_paciente_por_nome(self):
        await db_module.criar_paciente({"nome": "Carlos Lima"})
        await db_module.criar_paciente({"nome": "Beatriz Souza"})
        resultados = await db_module.listar_pacientes(busca="Carlos")
        assert len(resultados) == 1
        assert resultados[0]["nome"] == "Carlos Lima"

    async def test_buscar_paciente_por_cpf(self):
        await db_module.criar_paciente({"nome": "Maria", "cpf": "111.222.333-44"})
        resultados = await db_module.listar_pacientes(busca="111.222.333-44")
        assert len(resultados) == 1

    async def test_buscar_paciente_por_telefone(self):
        await db_module.criar_paciente({"nome": "João", "telefone": "(11) 99999-0000"})
        resultados = await db_module.listar_pacientes(busca="99999-0000")
        assert len(resultados) == 1

    async def test_atualizar_paciente(self):
        criado = await db_module.criar_paciente({"nome": "Nome Original"})
        atualizado = await db_module.atualizar_paciente(criado["id"], {"nome": "Nome Atualizado"})
        assert atualizado is not None
        assert atualizado["nome"] == "Nome Atualizado"

    async def test_atualizar_paciente_inexistente(self):
        resultado = await db_module.atualizar_paciente(99999, {"nome": "Teste"})
        assert resultado is None

    async def test_atualizar_paciente_sem_campos(self):
        criado = await db_module.criar_paciente({"nome": "Teste"})
        resultado = await db_module.atualizar_paciente(criado["id"], {})
        assert resultado is not None
        assert resultado["nome"] == "Teste"

    async def test_atualizar_paciente_cpf(self):
        criado = await db_module.criar_paciente({"nome": "Teste", "cpf": "000.000.000-00"})
        atualizado = await db_module.atualizar_paciente(criado["id"], {"cpf": "111.111.111-11"})
        assert atualizado["cpf"] == "111.111.111-11"

    async def test_deletar_paciente(self):
        criado = await db_module.criar_paciente({"nome": "Para Deletar"})
        ok = await db_module.deletar_paciente(criado["id"])
        assert ok is True
        obtido = await db_module.obter_paciente(criado["id"])
        assert obtido is None

    async def test_deletar_paciente_inexistente(self):
        ok = await db_module.deletar_paciente(99999)
        assert ok is False

    async def test_paciente_tem_timestamps(self):
        data = {"nome": "Teste Timestamps"}
        paciente = await db_module.criar_paciente(data)
        assert "created_at" in paciente
        assert "updated_at" in paciente
        assert paciente["created_at"] is not None
        assert paciente["updated_at"] is not None


@pytest.mark.asyncio
class TestAgendaCRUD:
    """Testa CRUD completo de agenda."""

    async def _criar_paciente(self, nome="Paciente Teste"):
        p = await db_module.criar_paciente({"nome": nome})
        return p["id"]

    async def test_criar_agendamento(self):
        pid = await self._criar_paciente()
        data = {
            "paciente_id": pid,
            "data_hora": "2026-06-15T14:30:00",
            "tipo": "consulta",
            "status": "agendado",
            "duracao_min": 30,
            "observacao": "Primeira consulta",
        }
        item = await db_module.criar_agendamento(data)
        assert item is not None
        assert item["paciente_id"] == pid
        assert item["status"] == "agendado"
        assert item["tipo"] == "consulta"

    async def test_criar_agendamento_padrao(self):
        pid = await self._criar_paciente()
        data = {
            "paciente_id": pid,
            "data_hora": "2026-06-15T14:30:00",
        }
        item = await db_module.criar_agendamento(data)
        assert item["tipo"] == "consulta"
        assert item["status"] == "agendado"
        assert item["duracao_min"] == 30

    async def test_obter_agendamento(self):
        pid = await self._criar_paciente()
        data = {"paciente_id": pid, "data_hora": "2026-06-15T14:30:00"}
        criado = await db_module.criar_agendamento(data)
        obtido = await db_module.obter_agendamento(criado["id"])
        assert obtido is not None
        assert obtido["paciente_id"] == pid

    async def test_obter_agendamento_inexistente(self):
        resultado = await db_module.obter_agendamento(99999)
        assert resultado is None

    async def test_listar_agenda_por_data(self):
        pid = await self._criar_paciente()
        await db_module.criar_agendamento({
            "paciente_id": pid, "data_hora": "2026-06-15T10:00:00"
        })
        await db_module.criar_agendamento({
            "paciente_id": pid, "data_hora": "2026-06-15T14:00:00"
        })
        await db_module.criar_agendamento({
            "paciente_id": pid, "data_hora": "2026-06-16T10:00:00"
        })
        itens = await db_module.listar_agenda(data="2026-06-15")
        assert len(itens) == 2

    async def test_listar_agenda_por_paciente(self):
        pid1 = await self._criar_paciente("Paciente A")
        pid2 = await self._criar_paciente("Paciente B")
        await db_module.criar_agendamento({
            "paciente_id": pid1, "data_hora": "2026-06-15T10:00:00"
        })
        await db_module.criar_agendamento({
            "paciente_id": pid2, "data_hora": "2026-06-15T14:00:00"
        })
        itens = await db_module.listar_agenda(paciente_id=pid1)
        assert len(itens) == 1
        assert itens[0]["paciente_id"] == pid1

    async def test_atualizar_agendamento(self):
        pid = await self._criar_paciente()
        data = {"paciente_id": pid, "data_hora": "2026-06-15T14:30:00"}
        criado = await db_module.criar_agendamento(data)
        atualizado = await db_module.atualizar_agendamento(
            criado["id"], {"status": "confirmado"}
        )
        assert atualizado["status"] == "confirmado"

    async def test_atualizar_agendamento_inexistente(self):
        resultado = await db_module.atualizar_agendamento(99999, {"status": "cancelado"})
        assert resultado is None

    async def test_deletar_agendamento(self):
        pid = await self._criar_paciente()
        data = {"paciente_id": pid, "data_hora": "2026-06-15T14:30:00"}
        criado = await db_module.criar_agendamento(data)
        ok = await db_module.deletar_agendamento(criado["id"])
        assert ok is True
        obtido = await db_module.obter_agendamento(criado["id"])
        assert obtido is None

    async def test_deletar_agendamento_inexistente(self):
        ok = await db_module.deletar_agendamento(99999)
        assert ok is False

    async def test_agenda_ordenada_por_data(self):
        pid = await self._criar_paciente()
        await db_module.criar_agendamento({
            "paciente_id": pid, "data_hora": "2026-06-16T10:00:00"
        })
        await db_module.criar_agendamento({
            "paciente_id": pid, "data_hora": "2026-06-15T10:00:00"
        })
        itens = await db_module.listar_agenda()
        assert len(itens) == 2
        assert itens[0]["data_hora"] < itens[1]["data_hora"]


class TestRowToDict:
    """Testa utilitário row_to_dict."""

    def test_row_none(self):
        assert db_module.row_to_dict(None) is None

    def test_row_dict(self):
        import aiosqlite

        async def check():
            async with aiosqlite.connect(":memory:") as db:
                db.row_factory = aiosqlite.Row
                await db.execute("CREATE TABLE t (id INTEGER, nome TEXT)")
                await db.execute("INSERT INTO t VALUES (1, 'teste')")
                await db.commit()
                row = await db.execute_fetchall("SELECT * FROM t")
                result = db_module.row_to_dict(row[0])
                assert isinstance(result, dict)
                assert result["id"] == 1
                assert result["nome"] == "teste"

        loop = asyncio.new_event_loop()
        loop.run_until_complete(check())
        loop.close()
