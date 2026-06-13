"""
OdontoAI — Backend FastAPI
Assistente Odontológico com voz + RAG

Stack:
  - STT: Whisper (CPU) ou Browser Web Speech API
  - TTS: edge-tts (gratuito, Microsoft)
  - LLM: OpenRouter API (gratuito) ou local
  - RAG: ChromaDB + embeddings leves
"""
import os
import io
import json
import time
import asyncio
import tempfile
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ==================== DATABASE ====================
from database import (
    init_db,
    listar_pacientes, obter_paciente, criar_paciente, atualizar_paciente, deletar_paciente,
    listar_agenda, obter_agendamento, criar_agendamento, atualizar_agendamento, deletar_agendamento,
    listar_prontuarios, obter_prontuario, criar_prontuario, atualizar_prontuario,
    listar_anamneses, obter_anamnese, criar_anamnese,
    obter_odontograma, criar_odontograma, atualizar_odontograma,
    listar_orcamentos, obter_orcamento, criar_orcamento,
    listar_financeiro, criar_financeiro,
    listar_alertas_pendentes, criar_alerta_retorno,
    salvar_conversa, listar_conversas,
)

# ==================== CONFIG ====================
BACKEND_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BACKEND_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"
AUDIO_DIR = BACKEND_DIR / "audio_cache"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = os.environ.get("ODONTO_MODEL", "openrouter/owl-alpha")  # Modelo padrão
# API key do OpenRouter via variável de ambiente (não commitada)
SERVER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# System prompt do agente odontológico
SYSTEM_PROMPT = """Você é o OdontoAI, um assistente de IA especializado em odontologia para dentistas brasileiros.

Suas funções:
1. AJUDAR COM PRONTUÁRIO — Registrar procedimentos, diagnósticos e observações ditados por voz
2. SUPORTE AO DIAGNÓSTICO — Sugerir diagnósticos diferenciais, nunca diagnóstico definitivo
3. CONHECIMENTO CLÍNICO — Responder dúvidas sobre odontologia com base em literatura
4. GESTÃO DE PACIENTES — Ajudar com lembretes, retornos, acompanhamento

Regras IMPORTANTES:
- Você é um ASSISTENTE, nunca substitui o dentista
- Sempre use frases como "sugiro", "considere", "pode ser"
- Para diagnósticos, sempre apresente diferenciais
- Use linguagem técnica odontológica em português do Brasil
- Seja conciso e prático — dentistas têm pouco tempo
- Nunca prescreva medicações sem ressalvas
- Quando não tiver certeza, diga que o dentista deve avaliar clinicamente

Responda de forma natural, como um colega experiente conversando."""

# ==================== CLIENT LLM ====================
from prontuario import extrair_entidades, formatar_prontuario, gerar_resposta_demo, buscar_conhecimento

async def call_llm(messages: list, api_key: str = "", model: str = DEFAULT_MODEL) -> str:
    """Chama LLM via OpenRouter. Usa key do usuário, ou key do servidor, ou demo."""
    
    # Prioridade: key do usuário > key do servidor > modo demo
    key = api_key or SERVER_API_KEY
    
    if not key:
        # Sem API key — modo demo com base de conhecimento local
        return gerar_resposta_demo(messages)
    
    import urllib.request
    
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024
    }).encode()
    
    req = urllib.request.Request(
        f"{OPENROUTER_BASE}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "HTTP-Referer": "https://odontoiap.com",
            "X-Title": "OdontoAI"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"LLM Error: {e}")
        return gerar_resposta_demo(messages)


# ==================== TTS (Text-to-Speech) ====================
async def tts_edge(text: str, voice: str = "pt-BR-FranciscaNeural") -> str:
    """Gera áudio usando edge-tts (gratuito, Microsoft)."""
    try:
        import edge_tts
        import hashlib
        
        # Cache por hash do texto
        text_hash = hashlib.md5(f"{voice}:{text}".encode()).hexdigest()
        output_path = AUDIO_DIR / f"{text_hash}.mp3"
        
        if output_path.exists():
            return str(output_path)
        
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
        
        return str(output_path)
    except ImportError:
        print("edge-tts não instalado")
        return ""
    except Exception as e:
        print(f"TTS Error: {e}")
        return ""


# ==================== STT (Speech-to-Text) ====================
_whisper_model = None

WHISPER_MODEL_SIZE = os.environ.get("ODONTO_WHISPER_MODEL", "base")

def load_whisper():
    """Carrega modelo faster-whisper sob demanda (CPU, int8)."""
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            print(f"Carregando faster-whisper (modelo {WHISPER_MODEL_SIZE}, CPU int8)...")
            _whisper_model = WhisperModel(
                WHISPER_MODEL_SIZE,
                device="cpu",
                compute_type="int8",
            )
            print("faster-whisper carregado!")
        except ImportError:
            print("faster-whisper não instalado. Use: pip install faster-whisper")
            return None
    return _whisper_model


async def stt_whisper(audio_path: str) -> str:
    """Transcreve áudio usando faster-whisper."""
    model = load_whisper()
    if model is None:
        return ""

    def _transcribe():
        # Converter para WAV primeiro (compatibilidade com WebM do navegador)
        import subprocess, os
        wav_path = audio_path + ".wav"
        try:
            result = subprocess.run([
                "ffmpeg", "-y", "-i", audio_path,
                "-ar", "16000", "-ac", "1", "-f", "wav", wav_path
            ], capture_output=True, timeout=30)
            if result.returncode == 0 and os.path.exists(wav_path) and os.path.getsize(wav_path) > 100:
                audio_path_final = wav_path
            else:
                audio_path_final = audio_path
        except Exception as e:
            print(f"FFmpeg conversion error: {e}")
            audio_path_final = audio_path

        try:
            segments, _info = model.transcribe(
                audio_path_final,
                language="pt",
                beam_size=5,
                vad_filter=True,
            )
            return "".join(seg.text for seg in segments).strip()
        except Exception as e:
            print(f"Whisper transcription error: {e}")
            return ""
        finally:
            # Limpar WAV temporário
            if audio_path_final != audio_path and os.path.exists(audio_path_final):
                os.unlink(audio_path_final)

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _transcribe)


# ==================== FASTAPI APP ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup e shutdown."""
    print("🦷 OdontoAI Backend iniciando...")
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    # Verificar dependências
    try:
        import edge_tts
        print("✅ edge-tts: OK")
    except ImportError:
        print("⚠️ edge-tts: NÃO INSTALADO (pip install edge-tts)")
    
    try:
        import faster_whisper
        print("✅ whisper: OK (faster-whisper)")
    except ImportError:
        print("⚠️ whisper: NÃO INSTALADO (pip install faster-whisper)")
    
    try:
        import chromadb
        print("✅ chromadb: OK")
    except ImportError:
        print("⚠️ chromadb: NÃO INSTALADO (pip install chromadb)")
    
    # Inicializar banco de dados
    try:
        await init_db()
        print("✅ database: OK")
    except Exception as e:
        print(f"⚠️ database: {e}")

    yield
    print("🦷 OdontoAI Backend encerrando...")


app = FastAPI(title="OdontoAI", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Arquivos estáticos
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ==================== ENDPOINTS ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve o PWA frontend."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text())
    return HTMLResponse("<h1>OdontoAI — Frontend não encontrado</h1><p>Copie a pasta frontend/ para o diretório correto.</p>")


@app.get("/manifest.json")
async def manifest():
    """PWA manifest."""
    manifest_path = FRONTEND_DIR / "manifest.json"
    if manifest_path.exists():
        return FileResponse(str(manifest_path))
    return {}


@app.get("/sw.js")
async def service_worker():
    """PWA service worker."""
    sw_path = FRONTEND_DIR / "sw.js"
    if sw_path.exists():
        return FileResponse(str(sw_path), media_type="application/javascript")
    return {}


@app.get("/api/health")
async def health():
    """Health check."""
    import edge_tts
    deps = {"edge_tts": True}
    try:
        import faster_whisper
        deps["whisper"] = True
    except ImportError:
        deps["whisper"] = False
    
    try:
        import chromadb
        deps["chromadb"] = True
    except ImportError:
        deps["chromadb"] = False
    
    return {"status": "ok", "service": "OdontoAI", "version": "0.1.0", "dependencies": deps}


class ChatRequest(BaseModel):
    message: str
    api_key: str = ""
    tts_voice: str = "pt-BR-FranciscaNeural"
    model: str = DEFAULT_MODEL


async def responder_com_rag(mensagem: str, api_key: str, modelo: str):
    """Busca contexto RAG nos livros e chama o LLM. Retorna (response, fontes)."""
    rag = get_rag()
    if not rag._loaded:
        rag.load()

    contexto_livros = ""
    fontes = []
    try:
        resultados = rag.search(mensagem, top_k=3)
        if resultados:
            trechos = []
            for r in resultados:
                if r["score"] > 0.1:  # Só usar trechos relevantes
                    trechos.append(f"[Fonte: {r['source']}]\n{r['text']}")
                    fontes.append(r["source"])
            if trechos:
                contexto_livros = "\n\n".join(trechos)
    except Exception as e:
        print(f"RAG search error: {e}")

    system_content = SYSTEM_PROMPT
    if contexto_livros:
        system_content += f"""

CONTEXTO DA LITERATURA ODONTOLÓGICA (use para fundamentar sua resposta):
{contexto_livros}

Use o contexto acima para embasar sua resposta quando relevante. Cite a fonte quando usar uma informação específica. Se o contexto não for relevante para a pergunta, responda com seu conhecimento geral."""

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": mensagem}
    ]
    response = await call_llm(messages, api_key, modelo)
    return response, list(set(fontes)) if fontes else []


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Endpoint de chat por texto, com RAG dos livros odontológicos."""

    modelo = request.model or DEFAULT_MODEL
    response, fontes = await responder_com_rag(request.message, request.api_key, modelo)

    # Gerar TTS
    audio_path = await tts_edge(response, request.tts_voice)
    audio_url = ""
    if audio_path:
        audio_hash = Path(audio_path).stem
        audio_url = f"/audio/{audio_hash}.mp3"

    return {
        "response": response,
        "audio_url": audio_url,
        "model": modelo if (request.api_key or SERVER_API_KEY) else "demo",
        "fontes": fontes
    }


@app.post("/api/voice")
async def voice(
    audio: UploadFile = File(...),
    api_key: str = Form(""),
    tts_voice: str = Form("pt-BR-FranciscaNeural"),
    stt_mode: str = Form("server"),
    model: str = Form(DEFAULT_MODEL)
):
    """Endpoint de chat por voz: recebe áudio, transcreve, responde."""
    
    start_time = time.time()
    
    # Salvar áudio temporariamente
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    # STT — transcrever
    if stt_mode == "server":
        transcription = await stt_whisper(tmp_path)
    else:
        transcription = ""  # Browser faz STT via Web Speech API
    
    # Limpar arquivo temporário
    os.unlink(tmp_path)
    
    modelo = model or DEFAULT_MODEL
    fontes = []
    if not transcription:
        transcription = "Não foi possível transcrever o áudio. Tente novamente."
        response = "Desculpe, não consegui entender o que você disse. Pode repetir?"
    else:
        # Responder com RAG (igual ao /api/chat)
        response, fontes = await responder_com_rag(transcription, api_key, modelo)

    # Gerar TTS
    audio_path = await tts_edge(response, tts_voice)
    audio_url = ""
    if audio_path:
        audio_hash = Path(audio_path).stem
        audio_url = f"/audio/{audio_hash}.mp3"

    elapsed = round(time.time() - start_time, 2)

    return {
        "transcription": transcription,
        "response": response,
        "audio_url": audio_url,
        "processing_time": elapsed,
        "model": modelo if (api_key or SERVER_API_KEY) else "demo",
        "fontes": fontes
    }


# ========== WEBSOCKET VOICE STREAMING ==========

@app.websocket("/api/voice/stream")
async def voice_stream(websocket: WebSocket):
    """
    WebSocket para streaming de voz contínuo (conversa ao vivo).
    
    Protocolo (JSON frames):
      Client -> Server:
        {"type": "audio", "data": "<base64 webm chunk>"}
        {"type": "config", "stt_mode": "server", "tts_voice": "pt-BR-FranciscaNeural"}
        {"type": "stop"}  # encerra a gravação do turno atual
      
      Server -> Client:
        {"type": "transcription", "text": "..."}
        {"type": "response", "text": "...", "fontes": [...]}
        {"type": "audio", "data": "<base64 mp3>"}
        {"type": "error", "message": "..."}
        {"type": "typing"}  # indica que está processando
    """
    await websocket.accept()
    print("🔌 WebSocket voice stream conectado")
    
    # Buffer de áudio do turno atual
    audio_buffer = bytearray()
    tts_voice = "pt-BR-FranciscaNeural"
    modelo = DEFAULT_MODEL
    
    try:
        while True:
            # Receber mensagem do cliente
            msg = await websocket.receive_json()
            msg_type = msg.get("type", "")
            
            if msg_type == "config":
                tts_voice = msg.get("tts_voice", tts_voice)
                modelo = msg.get("model", modelo)
                await websocket.send_json({"type": "ready", "message": "Configurado"})
            
            elif msg_type == "audio":
                # Acumular chunk de áudio
                import base64
                chunk = base64.b64decode(msg.get("data", ""))
                audio_buffer.extend(chunk)
            
            elif msg_type == "stop":
                # Processar o turno completo
                if len(audio_buffer) < 1000:
                    await websocket.send_json({"type": "error", "message": "Áudio muito curto"})
                    audio_buffer.clear()
                    continue
                
                await websocket.send_json({"type": "typing"})
                
                # Salvar buffer como arquivo temporário
                import base64
                tmp = tempfile.NamedTemporaryFile(suffix=".webm", delete=False)
                tmp.write(bytes(audio_buffer))
                tmp_path = tmp.name
                tmp.close()
                audio_buffer.clear()
                
                print(f"📁 Arquivo WebM salvo: {tmp_path} ({os.path.getsize(tmp_path)} bytes)")
                
                try:
                    # STT
                    transcription = await stt_whisper(tmp_path)
                    
                    if not transcription:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Não foi possível transcrever o áudio"
                        })
                        continue
                    
                    await websocket.send_json({
                        "type": "transcription",
                        "text": transcription
                    })
                    
                    # LLM com RAG
                    response, fontes = await responder_com_rag(
                        transcription, SERVER_API_KEY, modelo
                    )
                    
                    await websocket.send_json({
                        "type": "response",
                        "text": response,
                        "fontes": fontes
                    })
                    
                    # TTS
                    audio_path = await tts_edge(response, tts_voice)
                    if audio_path:
                        with open(audio_path, "rb") as f:
                            audio_b64 = base64.b64encode(f.read()).decode()
                        await websocket.send_json({
                            "type": "audio",
                            "data": audio_b64
                        })
                
                finally:
                    os.unlink(tmp_path)
    
    except WebSocketDisconnect:
        print("🔌 WebSocket voice stream desconectado")
    except Exception as e:
        print(f"❌ Erro no voice stream: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve arquivos de áudio gerados."""
    file_path = AUDIO_DIR / filename
    if file_path.exists():
        return FileResponse(str(file_path), media_type="audio/mpeg")
    return {"error": "Arquivo não encontrado"}


# ========== ENDPOINTS DE PRONTUÁRIO ==========

class ProntuarioRequest(BaseModel):
    texto: str


@app.post("/api/prontuario/extrair")
async def extrair_prontario(request: ProntuarioRequest):
    """Extrai entidades de prontuário de um texto livre."""
    entidades = extrair_entidades(request.texto)
    formato = formatar_prontuario(entidades)
    return {
        "entidades": {
            "dente": entidades.dente,
            "face": entidades.face,
            "procedimento": entidades.procedimento,
            "material": entidades.material,
            "diagnostico": entidades.diagnostico,
            "classificacao_angle": entidades.classificacao_angle,
            "observacoes": entidades.observacoes
        },
        "formatado": formato
    }


@app.post("/api/prontuario/conhecimento")
async def conhecimento_odontologico(request: ProntuarioRequest):
    """Busca conhecimento odontológico por palavras-chave."""
    resultado = buscar_conhecimento(request.texto)
    if resultado:
        return {"encontrado": True, "conteudo": resultado}
    
    # Fallback: usar o LLM demo
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request.texto}
    ]
    resposta = gerar_resposta_demo(messages)
    return {"encontrado": False, "conteudo": resposta}


# ========== MODELOS PACIENTES ==========

class PacienteCreate(BaseModel):
    nome: str
    cpf: Optional[str] = None
    data_nascimento: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    convenio: Optional[str] = None
    alergias: Optional[str] = None
    medicamentos: Optional[str] = None
    observacoes: Optional[str] = None


class PacienteUpdate(BaseModel):
    nome: Optional[str] = None
    cpf: Optional[str] = None
    data_nascimento: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    convenio: Optional[str] = None
    alergias: Optional[str] = None
    medicamentos: Optional[str] = None
    observacoes: Optional[str] = None


class AgendaCreate(BaseModel):
    paciente_id: int
    data_hora: str
    tipo: str = "consulta"
    status: str = "agendado"
    duracao_min: int = 30
    observacao: Optional[str] = None


class AgendaUpdate(BaseModel):
    paciente_id: Optional[int] = None
    data_hora: Optional[str] = None
    tipo: Optional[str] = None
    status: Optional[str] = None
    duracao_min: Optional[int] = None
    observacao: Optional[str] = None
    lembrete_enviado: Optional[int] = None


# ========== ENDPOINTS PACIENTES ==========


@app.get("/api/pacientes/busca")
async def buscar_pacientes(q: str = ""):
    """Busca pacientes por nome, CPF ou telefone."""
    resultados = await listar_pacientes(busca=q)
    return {"resultados": resultados, "total": len(resultados)}


@app.get("/api/pacientes")
async def get_pacientes(limit: int = 100, offset: int = 0):
    """Lista todos os pacientes."""
    pacientes = await listar_pacientes(limit=limit, offset=offset)
    return {"pacientes": pacientes, "total": len(pacientes)}


@app.get("/api/pacientes/{paciente_id}")
async def get_paciente(paciente_id: int):
    """Obtém um paciente por ID."""
    paciente = await obter_paciente(paciente_id)
    if not paciente:
        return {"error": "Paciente não encontrado"}, 404
    return paciente


@app.post("/api/pacientes")
async def post_paciente(data: PacienteCreate):
    """Cria um novo paciente."""
    paciente = await criar_paciente(data.model_dump())
    return paciente


@app.put("/api/pacientes/{paciente_id}")
async def put_paciente(paciente_id: int, data: PacienteUpdate):
    """Atualiza um paciente existente."""
    paciente = await atualizar_paciente(paciente_id, data.model_dump(exclude_none=True))
    if not paciente:
        return {"error": "Paciente não encontrado"}, 404
    return paciente


@app.delete("/api/pacientes/{paciente_id}")
async def delete_paciente(paciente_id: int):
    """Remove um paciente."""
    ok = await deletar_paciente(paciente_id)
    if not ok:
        return {"error": "Paciente não encontrado"}, 404
    return {"message": "Paciente removido com sucesso"}


# ========== ENDPOINTS AGENDA ==========


@app.get("/api/agenda/dia")
async def get_agenda_dia(date: str = ""):
    """Lista agendamentos de um dia específico (YYYY-MM-DD)."""
    itens = await listar_agenda(data=date)
    return {"agenda": itens, "total": len(itens)}


@app.get("/api/agenda")
async def get_agenda(paciente_id: int = None, limit: int = 100, offset: int = 0):
    """Lista agendamentos com filtros opcionais."""
    itens = await listar_agenda(paciente_id=paciente_id, limit=limit, offset=offset)
    return {"agenda": itens, "total": len(itens)}


@app.get("/api/agenda/{agenda_id}")
async def get_agendamento(agenda_id: int):
    """Obtém um agendamento por ID."""
    item = await obter_agendamento(agenda_id)
    if not item:
        return {"error": "Agendamento não encontrado"}, 404
    return item


@app.post("/api/agenda")
async def post_agendamento(data: AgendaCreate):
    """Cria um novo agendamento."""
    item = await criar_agendamento(data.model_dump())
    return item


@app.put("/api/agenda/{agenda_id}")
async def put_agendamento(agenda_id: int, data: AgendaUpdate):
    """Atualiza um agendamento existente."""
    item = await atualizar_agendamento(agenda_id, data.model_dump(exclude_none=True))
    if not item:
        return {"error": "Agendamento não encontrado"}, 404
    return item


@app.delete("/api/agenda/{agenda_id}")
async def delete_agendamento(agenda_id: int):
    """Remove um agendamento."""
    ok = await deletar_agendamento(agenda_id)
    if not ok:
        return {"error": "Agendamento não encontrado"}, 404
    return {"message": "Agendamento removido com sucesso"}


# ==================== PRONTUÁRIO ENDPOINTS ====================

# --- Prontuários ---

@app.get("/api/pacientes/{paciente_id}/prontuarios")
async def get_prontuarios_paciente(paciente_id: int):
    """Lista todos os prontuários de um paciente."""
    prontuarios = await listar_prontuarios(paciente_id)
    return {"prontuarios": prontuarios, "total": len(prontuarios)}


@app.get("/api/prontuarios/{prontuario_id}")
async def get_prontuario(prontuario_id: int):
    """Obtém um prontuário completo por ID."""
    item = await obter_prontuario(prontuario_id)
    if not item:
        return {"error": "Prontuário não encontrado"}, 404
    return item


class ProntuarioCreate(BaseModel):
    paciente_id: int
    profissional_id: int
    data_consulta: str
    motivo_consulta: str = ""
    diagnostico: str = ""
    cid: str = ""
    plano_tratamento: str = ""
    procedimentos: list = []
    evolucao: str = ""
    prescricoes: list = []
    atestado: str = ""
    retorno_data: str = ""
    retorno_motivo: str = ""
    observacoes: str = ""


@app.post("/api/prontuarios")
async def post_prontuario(data: ProntuarioCreate):
    """Cria um novo prontuário (ficha clínica)."""
    item = await criar_prontuario(data.model_dump())
    return item


class ProntuarioUpdate(BaseModel):
    motivo_consulta: str = None
    diagnostico: str = None
    cid: str = None
    plano_tratamento: str = None
    procedimentos: list = None
    evolucao: str = None
    prescricoes: list = None
    atestado: str = None
    retorno_data: str = None
    retorno_motivo: str = None
    observacoes: str = None


@app.put("/api/prontuarios/{prontuario_id}")
async def put_prontuario(prontuario_id: int, data: ProntuarioUpdate):
    """Atualiza um prontuário existente."""
    item = await atualizar_prontuario(prontuario_id, data.model_dump(exclude_none=True))
    if not item:
        return {"error": "Prontuário não encontrado"}, 404
    return item


# --- Anamneses ---

@app.get("/api/pacientes/{paciente_id}/anamneses")
async def get_anamneses_paciente(paciente_id: int):
    """Lista todas as anamneses de um paciente."""
    anamneses = await listar_anamneses(paciente_id)
    return {"anamneses": anamneses, "total": len(anamneses)}


@app.get("/api/anamneses/{anamnese_id}")
async def get_anamnese(anamnese_id: int):
    """Obtém uma anamnese por ID."""
    item = await obter_anamnese(anamnese_id)
    if not item:
        return {"error": "Anamnese não encontrada"}, 404
    return item


class AnamneseCreate(BaseModel):
    paciente_id: int
    profissional_id: int
    modo: str = "profissional"
    respostas: dict = {}
    alertas: list = []
    assinatura_paciente: str = ""
    observacoes: str = ""


@app.post("/api/anamneses")
async def post_anamnese(data: AnamneseCreate):
    """Cria uma nova anamnese."""
    item = await criar_anamnese(data.model_dump())
    return item


# --- Odontogramas ---

@app.get("/api/pacientes/{paciente_id}/odontograma")
async def get_odontograma_paciente(paciente_id: int):
    """Obtém o odontograma mais recente de um paciente."""
    item = await obter_odontograma(paciente_id)
    if not item:
        return {"error": "Odontograma não encontrado"}, 404
    return item


class OdontogramaCreate(BaseModel):
    paciente_id: int
    prontuario_id: int = None
    tipo_denticao: str = "permanente"
    dentes: dict = {}


@app.post("/api/odontogramas")
async def post_odontograma(data: OdontogramaCreate):
    """Cria um novo odontograma."""
    item = await criar_odontograma(data.model_dump())
    return item


class OdontogramaUpdate(BaseModel):
    dentes: dict


@app.put("/api/odontogramas/{odontograma_id}")
async def put_odontograma(odontograma_id: int, data: OdontogramaUpdate):
    """Atualiza um odontograma (marca procedimentos nos dentes)."""
    ok = await atualizar_odontograma(odontograma_id, data.dentes)
    if not ok:
        return {"error": "Odontograma não encontrado"}, 404
    return {"message": "Odontograma atualizado"}


# --- Orçamentos ---

@app.get("/api/pacientes/{paciente_id}/orcamentos")
async def get_orcamentos_paciente(paciente_id: int):
    """Lista orçamentos de um paciente."""
    orcamentos = await listar_orcamentos(paciente_id=paciente_id)
    return {"orcamentos": orcamentos, "total": len(orcamentos)}


@app.get("/api/orcamentos/{orcamento_id}")
async def get_orcamento(orcamento_id: int):
    """Obtém um orçamento por ID."""
    item = await obter_orcamento(orcamento_id)
    if not item:
        return {"error": "Orçamento não encontrado"}, 404
    return item


class OrcamentoCreate(BaseModel):
    paciente_id: int
    profissional_id: int = None
    itens: list = []
    valor_total: float = 0
    desconto: float = 0
    desconto_tipo: str = None
    valor_final: float = 0
    forma_pagamento: str = None
    parcelas: int = 1
    validade: str = None
    observacoes: str = ""


@app.post("/api/orcamentos")
async def post_orcamento(data: OrcamentoCreate):
    """Cria um novo orçamento."""
    item = await criar_orcamento(data.model_dump())
    return item


# --- Alertas de Retorno ---

@app.get("/api/alertas/retorno")
async def get_alertas_retorno():
    """Lista alertas de retorno pendentes."""
    alertas = await listar_alertas_pendentes()
    return {"alertas": alertas, "total": len(alertas)}


class AlertaRetornoCreate(BaseModel):
    paciente_id: int
    prontuario_id: int = None
    data_sugerida: str
    periodo: str = ""
    motivo: str = ""


@app.post("/api/alertas/retorno")
async def post_alerta_retorno(data: AlertaRetornoCreate):
    """Cria um alerta de retorno."""
    item = await criar_alerta_retorno(data.model_dump())
    return item


# ==================== LIVEKIT INTEGRATION ====================
from livekit_integration import router as livekit_router
app.include_router(livekit_router)

# ==================== RAG ENGINE ====================
from rag import get_rag

@app.on_event("startup")
async def load_rag():
    """Carrega o RAG engine no startup."""
    try:
        rag = get_rag()
        rag.load()
    except Exception as e:
        print(f"⚠️ RAG: {e}")


@app.get("/api/rag/search")
async def rag_search(q: str = "", top_k: int = 5):
    """Busca conhecimento odontológico nos livros."""
    rag = get_rag()
    if not rag._loaded:
        rag.load()
    results = rag.search(q, top_k=top_k)
    return {"query": q, "results": results, "total": len(results)}


class RAGSearchRequest(BaseModel):
    query: str
    top_k: int = 5


@app.post("/api/rag/search")
async def rag_search_post(request: RAGSearchRequest):
    """Busca conhecimento odontológico (POST)."""
    rag = get_rag()
    if not rag._loaded:
        rag.load()
    results = rag.search(request.query, top_k=request.top_k)
    return {"query": request.query, "results": results, "total": len(results)}


# ==================== MAIN ====================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"\n🦷 OdontoAI rodando em http://0.0.0.0:{port}")
    print(f"   Frontend: http://0.0.0.0:{port}/")
    print(f"   Health:   http://0.0.0.0:{port}/api/health\n")
    uvicorn.run(
        app, host="0.0.0.0", port=port, log_level="info",
        ws_ping_interval=30, ws_ping_timeout=120,
        timeout_keep_alive=120,
    )
