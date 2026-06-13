#!/bin/bash
# OdontoAI - Script de inicialização do backend
# Carrega a API key do OpenRouter e inicia o FastAPI

cd /opt/data/home/dentista-agente-prototipo/backend

# Carregar todas as variáveis do .env
if [ -f /opt/data/.env ]; then
  set -a
  source /opt/data/.env
  set +a
fi

# Modelo padrão: owl-alpha
export ODONTO_MODEL="${ODONTO_MODEL:-openrouter/owl-alpha}"

# Modelo Whisper (STT)
export ODONTO_WHISPER_MODEL="${ODONTO_WHISPER_MODEL:-medium}"

# LiveKit
export LIVEKIT_WS_URL="${LIVEKIT_WS_URL:-ws://localhost:7880}"

# Matar instância anterior (fuser; lsof não existe no container)
fuser -k 8080/tcp 2>/dev/null
sleep 2

echo "🦷 Iniciando OdontoAI backend..."
echo "   Modelo: $ODONTO_MODEL"
echo "   API key: ${OPENROUTER_API_KEY:0:12}..."

python3 main.py
