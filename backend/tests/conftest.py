"""
OdontoAI — Shared test fixtures.
"""
import os
import sys
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

# Garante que o backend/ está no path
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))


import pytest
import pytest_asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Cria um event loop para toda a sessão de testes."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Diretório temporário para testes."""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def sample_paciente():
    """Dados de exemplo para criar paciente."""
    return {
        "nome": "Maria da Silva",
        "cpf": "123.456.789-00",
        "data_nascimento": "1990-05-15",
        "telefone": "(11) 99999-1234",
        "email": "maria@email.com",
        "convenio": "Uniodonto",
        "alergias": "Látex",
        "medicamentos": "Losartana 50mg",
        "observacoes": "Paciente com hipertensão controlada",
    }


@pytest.fixture
def sample_paciente_minimal():
    """Dados mínimos para criar paciente (só nome)."""
    return {"nome": "João Santos"}


@pytest.fixture
def sample_agenda():
    """Dados de exemplo para agendamento."""
    return {
        "paciente_id": 1,
        "data_hora": "2026-06-15T14:30:00",
        "tipo": "consulta",
        "status": "agendado",
        "duracao_min": 30,
        "observacao": "Primeira consulta",
    }


@pytest_asyncio.fixture
async def test_db():
    """Cria banco de dados temporário compartilhado para testes de DB."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_odontoiap.db"

    import database as db_module
    original_path = db_module.DB_PATH
    original_dir = db_module.DB_DIR
    db_module.DB_PATH = db_path
    db_module.DB_DIR = Path(temp_dir)

    await db_module.init_db()

    yield db_path

    # Cleanup
    db_module.DB_PATH = original_path
    db_module.DB_DIR = original_dir
    shutil.rmtree(temp_dir, ignore_errors=True)
