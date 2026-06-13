"""
OdontoAI — LiveKit Voice Agent
Agente de voz em tempo real usando LiveKit + OpenRouter (LLM) + faster-whisper (STT) + edge-tts (TTS).

Arquitetura:
  1. Paciente/Dentista conecta via WebSocket (LiveKit Room)
  2. Áudio capturado → STT (faster-whisper) → Texto
  3. Texto + contexto → RAG (ChromaDB) → Contexto relevante
  4. Texto + contexto → LLM (OpenRouter) → Resposta
  5. Resposta → TTS (edge-tts) → Áudio
  6. Áudio enviado de volta ao cliente via LiveKit

Dependências:
  - livekit, livekit-agents, livekit-plugins-openai, livekit-plugins-silero
  - faster-whisper, edge-tts
"""
import os
import json
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

from livekit import agents, rtc
from livekit.agents import Agent, AgentSession, RoomInputOptions, RoomOutputOptions
from livekit.plugins import openai as lk_openai, silero

# ==================== CONFIG ====================

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = os.environ.get("ODONTO_MODEL", "openrouter/owl-alpha")
SERVER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
WHISPER_MODEL_SIZE = os.environ.get("ODONTO_WHISPER_MODEL", "medium")
TTS_VOICE = os.environ.get("ODONTO_TTS_VOICE", "pt-BR-FranciscaNeural")

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


# ==================== STT (faster-whisper) ====================

class WhisperSTT:
    """STT usando faster-whisper (local, CPU)."""
    
    def __init__(self, model_size: str = "medium"):
        self.model_size = model_size
        self._model = None
    
    def _load_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            print(f"Carregando faster-whisper (modelo {self.model_size}, CPU int8)...")
            self._model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
            )
        return self._model
    
    async def transcribe(self, audio_data: bytes, language: str = "pt") -> str:
        """Transcreve áudio (WAV/MP3) para texto."""
        model = self._load_model()
        
        # Salvar áudio temporariamente
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name
        
        try:
            segments, _ = model.transcribe(tmp_path, language=language, beam_size=5)
            text = " ".join(seg.text for seg in segments)
            return text.strip()
        finally:
            os.unlink(tmp_path)


# ==================== TTS (edge-tts) ====================

class EdgeTTS:
    """TTS usando edge-tts (gratuito, Microsoft)."""
    
    def __init__(self, voice: str = "pt-BR-FranciscaNeural"):
        self.voice = voice
        self._cache_dir = Path("/tmp/odontoiap_tts_cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def synthesize(self, text: str) -> bytes:
        """Sintetiza texto em áudio (MP3)."""
        import edge_tts
        import hashlib
        
        # Cache por hash do texto
        text_hash = hashlib.md5(f"{self.voice}:{text}".encode()).hexdigest()
        output_path = self._cache_dir / f"{text_hash}.mp3"
        
        if output_path.exists():
            return output_path.read_bytes()
        
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(str(output_path))
        
        return output_path.read_bytes()


# ==================== LLM (OpenRouter) ====================

async def call_llm(messages: list, api_key: str = "", model: str = DEFAULT_MODEL) -> str:
    """Chama LLM via OpenRouter."""
    import urllib.request
    
    key = api_key or SERVER_API_KEY
    if not key:
        return "Modo demo: configure uma API key do OpenRouter para ativar a IA."
    
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
        return "Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente."


# ==================== RAG ====================

async def buscar_contexto_rag(pergunta: str) -> tuple[str, list]:
    """Busca contexto RAG nos livros odontológicos. Retorna (contexto, fontes)."""
    try:
        from rag import get_rag
        rag = get_rag()
        if not rag._loaded:
            rag.load()
        
        resultados = rag.search(pergunta, top_k=3)
        if resultados:
            trechos = []
            fontes = []
            for r in resultados:
                if r.get("score", 0) > 0.1:
                    trechos.append(f"[Fonte: {r.get('source', 'N/A')}]\n{r.get('text', '')}")
                    fontes.append(r.get("source", "N/A"))
            if trechos:
                return "\n\n".join(trechos), list(set(fontes))
    except Exception as e:
        print(f"RAG Error: {e}")
    
    return "", []


# ==================== ODONTOAI AGENT ====================

class OdontoAIAgent(Agent):
    """Agente de voz OdontoAI para LiveKit."""
    
    def __init__(self):
        super().__init__(instructions=SYSTEM_PROMPT)
        self._whisper = WhisperSTT(WHISPER_MODEL_SIZE)
        self._tts = EdgeTTS(TTS_VOICE)
        self._conversation_history = []
    
    async def on_enter(self):
        """Chamado quando o agente entra na sala."""
        await self.session.generate_reply(
            instructions="Olá! Sou o OdontoAI, seu assistente odontológico. Como posso ajudar?"
        )
    
    async def on_user_turn_completed(self, chat_ctx: agents.ChatContext, new_message: agents.ChatMessage):
        """Processa a fala do usuário e gera resposta."""
        user_text = new_message.content
        
        # Buscar contexto RAG
        contexto, fontes = await buscar_contexto_rag(user_text)
        
        # Construir mensagens
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if contexto:
            messages[0]["content"] += f"\n\nCONTEXTO DA LITERATURA:\n{contexto}"
        
        # Adicionar histórico recente (últimas 10 mensagens)
        for msg in self._conversation_history[-10:]:
            messages.append(msg)
        
        messages.append({"role": "user", "content": user_text})
        
        # Chamar LLM
        response = await call_llm(messages)
        
        # Salvar no histórico
        self._conversation_history.append({"role": "user", "content": user_text})
        self._conversation_history.append({"role": "assistant", "content": response})
        
        # Gerar TTS
        audio_bytes = await self._tts.synthesize(response)
        
        # Enviar resposta
        await self.session.say(response)
        
        return response


# ==================== LIVEKIT WORKER ====================

async def entrypoint(ctx: agents.JobContext):
    """Entrypoint do LiveKit Worker."""
    print("🦷 OdontoAI LiveKit Worker iniciado")
    
    # Criar sessão do agente
    session = AgentSession(
        stt=lk_openai.STT.with_openai(
            base_url=OPENROUTER_BASE,
            api_key=SERVER_API_KEY,
        ) if SERVER_API_KEY else None,
        llm=lk_openai.LLM.with_openai(
            base_url=OPENROUTER_BASE,
            api_key=SERVER_API_KEY,
        ) if SERVER_API_KEY else None,
        tts=lk_openai.TTS.with_openai(
            base_url=OPENROUTER_BASE,
            api_key=SERVER_API_KEY,
        ) if SERVER_API_KEY else None,
        vad=silero.VAD.load(),
    )
    
    # Criar agente
    agent = OdontoAIAgent()
    
    # Conectar à sala
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=True,
        ),
        room_output_options=RoomOutputOptions(
            transcription_enabled=True,
        ),
    )
    
    print(f"✅ Agente conectado à sala: {ctx.room.name}")


# ==================== MAIN ====================

if __name__ == "__main__":
    import sys
    
    # Rodar como LiveKit Worker
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=os.environ.get("LIVEKIT_API_KEY", ""),
            api_secret=os.environ.get("LIVEKIT_API_SECRET", ""),
            ws_url=os.environ.get("LIVEKIT_WS_URL", ""),
        )
    )
