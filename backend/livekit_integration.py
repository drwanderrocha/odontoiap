"""
OdontoAI — LiveKit Integration Module
Integração do LiveKit com o backend FastAPI existente.

Este módulo fornece:
1. Criação de tokens para conexão do cliente
2. Webhook para eventos do LiveKit
3. Agent worker para processamento de voz

Uso:
  - Rodar como worker separado: python livekit_agent.py
  - Ou via Docker: docker run livekit-agent

Variáveis de ambiente:
  - LIVEKIT_API_KEY: Chave API do LiveKit
  - LIVEKIT_API_SECRET: Segredo API do LiveKit
  - LIVEKIT_WS_URL: URL WebSocket do LiveKit (ex: wss://seu-projeto.livekit.cloud)
  - LIVEKIT_SERVER_URL: URL pública do LiveKit server (opcional, para self-hosted)
"""
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# LiveKit imports (instalados via pip)
try:
    from livekit import api as lk_api
    from livekit import agents, rtc
    from livekit.agents import Agent, AgentSession
    from livekit.plugins import openai as lk_openai, silero
    LIVEKIT_AVAILABLE = True
except ImportError:
    LIVEKIT_AVAILABLE = False
    print("⚠️ LiveKit não instalado. Instale com: pip install livekit livekit-agents livekit-plugins-openai livekit-plugins-silero")

# ==================== CONFIG ====================

LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "")
LIVEKIT_WS_URL = os.environ.get("LIVEKIT_WS_URL", "")
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
SERVER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
DEFAULT_MODEL = os.environ.get("ODONTO_MODEL", "openrouter/owl-alpha")
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


# ==================== ROUTER ====================

router = APIRouter(prefix="/api/livekit", tags=["livekit"])


class TokenRequest(BaseModel):
    room_name: str
    participant_name: str
    metadata: str = ""


class RoomRequest(BaseModel):
    room_name: str
    max_participants: int = 10


@router.get("/status")
async def livekit_status():
    """Verifica se o LiveKit está configurado."""
    return {
        "livekit_available": LIVEKIT_AVAILABLE,
        "configured": bool(LIVEKIT_API_KEY and LIVEKIT_API_SECRET and LIVEKIT_WS_URL),
        "ws_url": LIVEKIT_WS_URL if LIVEKIT_WS_URL else "não configurado",
    }


@router.post("/token")
async def create_token(request: TokenRequest):
    """Cria um token para conexão do cliente ao LiveKit."""
    if not LIVEKIT_AVAILABLE:
        raise HTTPException(status_code=503, detail="LiveKit não instalado")
    
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(status_code=503, detail="LiveKit não configurado")
    
    try:
        token = lk_api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        token.with_identity(request.participant_name)
        token.with_name(request.participant_name)
        token.with_metadata(request.metadata)
        token.with_grants(lk_api.VideoGrants(
            room_join=True,
            room=request.room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        ))
        
        jwt = token.to_jwt()
        
        return {
            "token": jwt,
            "ws_url": LIVEKIT_WS_URL,
            "room_name": request.room_name,
            "participant_name": request.participant_name,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar token: {e}")


@router.post("/room")
async def create_room(request: RoomRequest):
    """Cria uma nova sala no LiveKit."""
    if not LIVEKIT_AVAILABLE:
        raise HTTPException(status_code=503, detail="LiveKit não instalado")
    
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(status_code=503, detail="LiveKit não configurado")
    
    try:
        room_service = lk_api.LiveKitAPI(
            url=LIVEKIT_WS_URL.replace("wss://", "https://").replace("ws://", "http://"),
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET,
        )
        
        room = await room_service.room.create_room(
            name=request.room_name,
            empty_timeout=300,  # 5 minutos
            max_participants=request.max_participants,
        )
        
        await room_service.aclose()
        
        return {
            "room_name": room.name,
            "created_at": str(room.creation_time),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar sala: {e}")


@router.delete("/room/{room_name}")
async def delete_room(room_name: str):
    """Remove uma sala do LiveKit."""
    if not LIVEKIT_AVAILABLE:
        raise HTTPException(status_code=503, detail="LiveKit não instalado")
    
    try:
        room_service = lk_api.LiveKitAPI(
            url=LIVEKIT_WS_URL.replace("wss://", "https://").replace("ws://", "http://"),
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET,
        )
        
        await room_service.room.delete_room(room_name)
        await room_service.aclose()
        
        return {"message": f"Sala {room_name} removida"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover sala: {e}")


# ==================== LIVEKIT AGENT ====================

class OdontoAIVoiceAgent(Agent):
    """Agente de voz OdontoAI para LiveKit Rooms."""
    
    def __init__(self):
        super().__init__(instructions=SYSTEM_PROMPT)
    
    async def on_enter(self):
        """Quando o agente entra na sala."""
        await self.session.generate_reply(
            instructions="Olá! Sou o OdontoAI, seu assistente odontológico. Como posso ajudar você hoje?"
        )


async def livekit_entrypoint(ctx: agents.JobContext):
    """Entrypoint do LiveKit Worker."""
    print(f"🦷 OdontoAI LiveKit Worker iniciado — Sala: {ctx.room.name}")
    
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
    
    agent = OdontoAIVoiceAgent()
    
    await session.start(
        agent=agent,
        room=ctx.room,
    )
    
    print(f"✅ Agente conectado à sala: {ctx.room.name}")


# ==================== WORKER RUNNER ====================

def run_livekit_worker():
    """Roda o LiveKit Worker (deve ser chamado em processo separado)."""
    if not LIVEKIT_AVAILABLE:
        print("❌ LiveKit não instalado")
        return
    
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET or not LIVEKIT_WS_URL:
        print("❌ LiveKit não configurado. Defina LIVEKIT_API_KEY, LIVEKIT_API_SECRET e LIVEKIT_WS_URL")
        return
    
    print("🦷 Iniciando OdontoAI LiveKit Worker...")
    print(f"   WS URL: {LIVEKIT_WS_URL}")
    print(f"   Modelo: {DEFAULT_MODEL}")
    
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=livekit_entrypoint,
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET,
            ws_url=LIVEKIT_WS_URL,
        )
    )


if __name__ == "__main__":
    run_livekit_worker()
