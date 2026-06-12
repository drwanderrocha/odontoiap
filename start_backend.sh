#!/bin/bash
# OdontoAI - Script de inicialização do backend
# Carrega a API key do OpenRouter e inicia o FastAPI

cd /opt/data/home/dentista-agente-prototipo/backend

# Carregar OPENROUTER_API_KEY do .env do Hermes
if [ -f /opt/data/.env ]; then
  export $(grep OPENROUTER_API_KEY /opt/data/.env | xargs)
fi

# Modelo padrão: owl-alpha
export ODONTO_MODEL="openrouter/owl-alpha"

# Modelo Whisper (STT). Opções: base, small, medium, large-v3. medium = melhor precisão para PT-BR.
export ODONTO_WHISPER_MODEL="medium"

# Matar instância anterior (fuser; lsof não existe no container)
fuser -k 8080/tcp 2>/dev/null
sleep 2

echo "🦷 Iniciando OdontoAI backend..."
echo "   Modelo: $ODONTO_MODEL"
echo "   API key: ${OPENROUTER_API_KEY:0:12}..."

python3 main.py
