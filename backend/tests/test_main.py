"""
Testes unitários para main.py (endpoints FastAPI)
Cobertura: health, chat, prontuario, pacientes, agenda, RAG search.
"""
import pytest
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

# ==================== SETUP DO AMBIENTE DE TESTE ====================
_temp_dir = tempfile.mkdtemp()
_db_path = Path(_temp_dir) / "test_odontoiap.db"

import database as db_module
_db_orig_path = db_module.DB_PATH
_db_orig_dir = db_module.DB_DIR
db_module.DB_PATH = _db_path
db_module.DB_DIR = Path(_temp_dir)

from main import app
from fastapi.testclient import TestClient

# Mock TTS global
import main as main_module
_orig_tts = main_module.tts_edge
main_module.tts_edge = AsyncMock(return_value="")

# Mock whisper
main_module._whisper_model = MagicMock()
main_module.load_whisper = lambda: MagicMock()

# Mock RAG
from rag import RAGEngine
_mock_rag = RAGEngine()
_mock_rag._loaded = True
_mock_rag.search = MagicMock(return_value=[])
_mock_rag.load = MagicMock()
main_module.get_rag = lambda: _mock_rag


@pytest.fixture(scope="session", autouse=True)
def _init_db():
    """Inicializa o banco de dados uma vez para todos os testes."""
    import asyncio
    loop = asyncio.new_event_loop()
    loop.run_until_complete(db_module.init_db())
    yield
    # Cleanup
    main_module.tts_edge = _orig_tts
    db_module.DB_PATH = _db_orig_path
    db_module.DB_DIR = _db_orig_dir
    shutil.rmtree(_temp_dir, ignore_errors=True)
    loop.close()


@pytest.fixture(autouse=True)
def clean_db():
    """Limpa tabelas antes de cada teste."""
    import asyncio

    async def _clean():
        async with db_module.get_db() as db:
            await db.execute("DELETE FROM agenda")
            await db.execute("DELETE FROM pacientes")
            await db.commit()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(_clean())
    loop.close()
    yield


# ==================== TESTES ====================

class TestHealthEndpoint:
    """Testa GET /api/health."""

    def test_health_status_ok(self):
        with TestClient(app) as client:
            response = client.get("/api/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["service"] == "OdontoAI"

    def test_health_tem_dependencias(self):
        with TestClient(app) as client:
            response = client.get("/api/health")
            data = response.json()
            assert "dependencies" in data
            assert "edge_tts" in data["dependencies"]
            assert "whisper" in data["dependencies"]
            assert "chromadb" in data["dependencies"]

    def test_health_versao(self):
        with TestClient(app) as client:
            response = client.get("/api/health")
            data = response.json()
            assert "version" in data


class TestChatEndpoint:
    """Testa POST /api/chat."""

    def test_chat_mensagem_simples(self):
        with TestClient(app) as client:
            response = client.post("/api/chat", json={
                "message": "Olá!",
                "api_key": "",
            })
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert len(data["response"]) > 0

    def test_chat_retorna_model_demo(self):
        with TestClient(app) as client:
            old_key = main_module.SERVER_API_KEY
            main_module.SERVER_API_KEY = ""
            try:
                response = client.post("/api/chat", json={"message": "Oi"})
                data = response.json()
                assert data["model"] == "demo"
            finally:
                main_module.SERVER_API_KEY = old_key

    def test_chat_com_pergunta_odonto(self):
        with TestClient(app) as client:
            response = client.post("/api/chat", json={
                "message": "O que é classe III de Angle?",
            })
            assert response.status_code == 200
            data = response.json()
            assert len(data["response"]) > 50

    def test_chat_com_prontuario(self):
        with TestClient(app) as client:
            response = client.post("/api/chat", json={
                "message": "Restauração em resina no dente 36, face oclusal",
            })
            assert response.status_code == 200
            data = response.json()
            assert "response" in data

    def test_chat_retorna_fontes(self):
        with TestClient(app) as client:
            response = client.post("/api/chat", json={"message": "Olá"})
            data = response.json()
            assert "fontes" in data
            assert isinstance(data["fontes"], list)

    def test_chat_retorna_audio_url(self):
        with TestClient(app) as client:
            response = client.post("/api/chat", json={"message": "Olá"})
            data = response.json()
            assert "audio_url" in data


class TestProntuarioEndpoint:
    """Testa POST /api/prontuario/extrair."""

    def test_extrair_entidades_completas(self):
        with TestClient(app) as client:
            response = client.post("/api/prontuario/extrair", json={
                "texto": "Restauração em resina composta no dente 36, face oclusal"
            })
            assert response.status_code == 200
            data = response.json()
            assert "entidades" in data
            assert "formatado" in data
            assert data["entidades"]["dente"] is not None
            assert "36" in data["entidades"]["dente"]
            assert data["entidades"]["procedimento"] == "Restauração"
            assert data["entidades"]["material"] == "Resina Composta"
            assert data["entidades"]["face"] == "Oclusal"

    def test_extrair_extracao(self):
        with TestClient(app) as client:
            response = client.post("/api/prontuario/extrair", json={
                "texto": "Extração do dente 48"
            })
            data = response.json()
            assert data["entidades"]["procedimento"] == "Extração"
            assert "48" in data["entidades"]["dente"]

    def test_extrair_canal(self):
        with TestClient(app) as client:
            response = client.post("/api/prontuario/extrair", json={
                "texto": "Tratamento de canal no 26"
            })
            data = response.json()
            assert data["entidades"]["procedimento"] == "Tratamento Endodôntico"

    def test_extrair_sem_entidades(self):
        with TestClient(app) as client:
            response = client.post("/api/prontuario/extrair", json={
                "texto": "Paciente veio para revisão"
            })
            data = response.json()
            assert data["entidades"]["dente"] is None
            assert data["entidades"]["procedimento"] is None

    def test_extrair_classificacao_angle(self):
        with TestClient(app) as client:
            response = client.post("/api/prontuario/extrair", json={
                "texto": "Paciente com classe I de Angle"
            })
            data = response.json()
            assert data["entidades"]["classificacao_angle"] is not None
            assert "Classe I" in data["entidades"]["classificacao_angle"]


class TestConhecimentoEndpoint:
    """Testa POST /api/prontuario/conhecimento."""

    def test_conhecimento_lesao_periapical(self):
        with TestClient(app) as client:
            response = client.post("/api/prontuario/conhecimento", json={
                "texto": "lesão periapical diagnóstico diferencial"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["encontrado"] is True
            assert len(data["conteudo"]) > 50

    def test_conhecimento_classe_iii(self):
        with TestClient(app) as client:
            response = client.post("/api/prontuario/conhecimento", json={
                "texto": "classe iii de angle tratamento"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["encontrado"] is True

    def test_conhecimento_nao_encontrado(self):
        with TestClient(app) as client:
            response = client.post("/api/prontuario/conhecimento", json={
                "texto": "xyzabc123 completamente desconhecido qwerty"
            })
            assert response.status_code == 200
            data = response.json()
            assert "encontrado" in data


class TestPacientesEndpoints:
    """Testa CRUD de pacientes via API."""

    def test_criar_paciente(self):
        with TestClient(app) as client:
            response = client.post("/api/pacientes", json={
                "nome": "Maria da Silva",
                "cpf": "123.456.789-00",
                "telefone": "(11) 99999-1234",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["nome"] == "Maria da Silva"
            assert data["id"] is not None

    def test_criar_paciente_minimo(self):
        with TestClient(app) as client:
            response = client.post("/api/pacientes", json={"nome": "João Santos"})
            assert response.status_code == 200
            data = response.json()
            assert data["nome"] == "João Santos"

    def test_listar_pacientes(self):
        with TestClient(app) as client:
            client.post("/api/pacientes", json={"nome": "Ana Costa"})
            client.post("/api/pacientes", json={"nome": "Carlos Lima"})
            response = client.get("/api/pacientes")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] >= 2

    def test_obter_paciente(self):
        with TestClient(app) as client:
            criado = client.post("/api/pacientes", json={"nome": "Teste Obter"})
            pid = criado.json()["id"]
            response = client.get(f"/api/pacientes/{pid}")
            assert response.status_code == 200
            data = response.json()
            assert data["nome"] == "Teste Obter"

    def test_obter_paciente_inexistente(self):
        with TestClient(app) as client:
            response = client.get("/api/pacientes/99999")
            assert response.status_code in (200, 404)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    assert "error" in data

    def test_atualizar_paciente(self):
        with TestClient(app) as client:
            criado = client.post("/api/pacientes", json={"nome": "Nome Original"})
            pid = criado.json()["id"]
            response = client.put(f"/api/pacientes/{pid}", json={"nome": "Nome Atualizado"})
            assert response.status_code == 200
            data = response.json()
            assert data["nome"] == "Nome Atualizado"

    def test_deletar_paciente(self):
        with TestClient(app) as client:
            criado = client.post("/api/pacientes", json={"nome": "Para Deletar"})
            pid = criado.json()["id"]
            response = client.delete(f"/api/pacientes/{pid}")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data

    def test_buscar_pacientes(self):
        with TestClient(app) as client:
            client.post("/api/pacientes", json={"nome": "Maria Silva"})
            client.post("/api/pacientes", json={"nome": "João Santos"})
            response = client.get("/api/pacientes/busca?q=Maria")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] >= 1


class TestAgendaEndpoints:
    """Testa CRUD de agenda via API."""

    def _criar_paciente(self, client, nome="Paciente Teste"):
        resp = client.post("/api/pacientes", json={"nome": nome})
        return resp.json()["id"]

    def test_criar_agendamento(self):
        with TestClient(app) as client:
            pid = self._criar_paciente(client)
            response = client.post("/api/agenda", json={
                "paciente_id": pid,
                "data_hora": "2026-06-15T14:30:00",
                "tipo": "consulta",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["paciente_id"] == pid
            assert data["status"] == "agendado"

    def test_listar_agenda(self):
        with TestClient(app) as client:
            pid = self._criar_paciente(client)
            client.post("/api/agenda", json={
                "paciente_id": pid,
                "data_hora": "2026-06-15T14:30:00",
            })
            response = client.get("/api/agenda")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] >= 1

    def test_listar_agenda_por_dia(self):
        with TestClient(app) as client:
            pid = self._criar_paciente(client)
            client.post("/api/agenda", json={
                "paciente_id": pid,
                "data_hora": "2026-06-15T10:00:00",
            })
            client.post("/api/agenda", json={
                "paciente_id": pid,
                "data_hora": "2026-06-16T10:00:00",
            })
            response = client.get("/api/agenda/dia?date=2026-06-15")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] >= 1

    def test_obter_agendamento(self):
        with TestClient(app) as client:
            pid = self._criar_paciente(client)
            criado = client.post("/api/agenda", json={
                "paciente_id": pid,
                "data_hora": "2026-06-15T14:30:00",
            })
            aid = criado.json()["id"]
            response = client.get(f"/api/agenda/{aid}")
            assert response.status_code == 200
            data = response.json()
            assert data["paciente_id"] == pid

    def test_atualizar_agendamento(self):
        with TestClient(app) as client:
            pid = self._criar_paciente(client)
            criado = client.post("/api/agenda", json={
                "paciente_id": pid,
                "data_hora": "2026-06-15T14:30:00",
            })
            aid = criado.json()["id"]
            response = client.put(f"/api/agenda/{aid}", json={"status": "confirmado"})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "confirmado"

    def test_deletar_agendamento(self):
        with TestClient(app) as client:
            pid = self._criar_paciente(client)
            criado = client.post("/api/agenda", json={
                "paciente_id": pid,
                "data_hora": "2026-06-15T14:30:00",
            })
            aid = criado.json()["id"]
            response = client.delete(f"/api/agenda/{aid}")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data


class TestRAGSearchEndpoint:
    """Testa GET/POST /api/rag/search."""

    def test_rag_search_get(self):
        with TestClient(app) as client:
            response = client.get("/api/rag/search?q=cárie&top_k=3")
            assert response.status_code == 200
            data = response.json()
            assert "query" in data
            assert "results" in data

    def test_rag_search_post(self):
        with TestClient(app) as client:
            response = client.post("/api/rag/search", json={
                "query": "restauração resina",
                "top_k": 3,
            })
            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "restauração resina"
            assert "results" in data


class TestRootEndpoint:
    """Testa GET / (frontend)."""

    def test_root_retorna_html(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")
