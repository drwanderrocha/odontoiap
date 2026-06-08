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

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ==================== CONFIG ====================
BACKEND_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BACKEND_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"
AUDIO_DIR = BACKEND_DIR / "audio_cache"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "google/gemini-2.0-flash-exp:free"  # Gratuito no OpenRouter

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
    """Chama LLM via OpenRouter (gratuito) ou fallback demo."""
    
    if not api_key:
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
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://odontoiap.com",
            "X-Title": "OdontoAI"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
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

def load_whisper():
    """Carrega modelo Whisper sob demanda."""
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            print("Carregando Whisper (modelo base)...")
            _whisper_model = whisper.load_model("base")
            print("Whisper carregado!")
        except ImportError:
            print("Whisper não instalado. Use: pip install openai-whisper")
            return None
    return _whisper_model


async def stt_whisper(audio_path: str) -> str:
    """Transcreve áudio usando Whisper."""
    model = load_whisper()
    if model is None:
        return ""
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, 
        lambda: model.transcribe(audio_path, language="pt")
    )
    return result.get("text", "").strip()


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
        import whisper
        print("✅ whisper: OK")
    except ImportError:
        print("⚠️ whisper: NÃO INSTALADO (pip install openai-whisper)")
    
    try:
        import chromadb
        print("✅ chromadb: OK")
    except ImportError:
        print("⚠️ chromadb: NÃO INSTALADO (pip install chromadb)")
    
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
        import whisper
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


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Endpoint de chat por texto."""
    
    # Montar mensagens
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request.message}
    ]
    
    # Chamar LLM
    response = await call_llm(messages, request.api_key, request.model)
    
    # Gerar TTS
    audio_path = await tts_edge(response, request.tts_voice)
    audio_url = ""
    if audio_path:
        audio_hash = Path(audio_path).stem
        audio_url = f"/audio/{audio_hash}.mp3"
    
    return {
        "response": response,
        "audio_url": audio_url,
        "model": request.model if request.api_key else "demo"
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
    
    if not transcription:
        transcription = "Não foi possível transcrever o áudio. Tente novamente."
        response = "Desculpe, não consegui entender o que você disse. Pode repetir?"
    else:
        # Chamar LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": transcription}
        ]
        response = await call_llm(messages, api_key, model)
    
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
        "model": model if api_key else "demo"
    }


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


# ==================== MAIN ====================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"\n🦷 OdontoAI rodando em http://0.0.0.0:{port}")
    print(f"   Frontend: http://0.0.0.0:{port}/")
    print(f"   Health:   http://0.0.0.0:{port}/api/health\n")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
