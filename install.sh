#!/bin/bash
# 🦷 OdontoAI — Script de Instalação do Protótipo
# Execute: bash install.sh

set -e

PROJECT_DIR="/opt/data/home/dentista-agente-prototipo"
BACKEND_DIR="$PROJECT_DIR/backend"

echo "========================================="
echo "  🦷 OdontoAI — Instalação"
echo "========================================="

# 1. Instalar dependências do sistema
echo ""
echo "[1/4] Instalando dependências do sistema..."
apt-get update -qq 2>/dev/null || true
apt-get install -y -qq python3-pip ffmpeg 2>/dev/null || {
    echo "⚠️ Erro ao instalar dependências do sistema (pode precisar de sudo)"
}

# 2. Instalar Python packages
echo ""
echo "[2/4] Instalando dependências Python..."
pip3 install --break-system-packages -q \
    fastapi uvicorn[standard] python-multipart edge-tts requests 2>/dev/null || \
pip install --break-system-packages -q \
    fastapi uvicorn[standard] python-multipart edge-tts requests 2>/dev/null || \
echo "⚠️ Erro ao instalar pacotes. Tente manual: pip install -r requirements.txt"

# 3. Criar diretórios
echo ""
echo "[3/4] Criando diretórios..."
mkdir -p "$PROJECT_DIR/audio_cache"
mkdir -p "$PROJECT_DIR/frontend/static"

# Verificar dependências
echo ""
echo "[4/4] Verificando instalação..."

PYTHON_CMD=""
for cmd in python3 python; do
    if command -v $cmd &>/dev/null; then
        PYTHON_CMD=$cmd
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python não encontrado!"
    exit 1
fi

echo "  Python: $($PYTHON_CMD --version)"

$PYTHON_CMD -c "import fastapi; echo '  FastAPI: OK'" 2>/dev/null || echo "  FastAPI: ❌"
$PYTHON_CMD -c "import uvicorn; echo '  Uvicorn: OK'" 2>/dev/null || echo "  Uvicorn: ❌"
$PYTHON_CMD -c "import edge_tts; echo '  edge-tts: OK'" 2>/dev/null || echo "  edge-tts: ⚠️ (opcional para TTS no servidor)"
$PYTHON_CMD -c "import whisper; echo '  Whisper: OK'" 2>/dev/null || echo "  Whisper: ⚠️ (opcional, precisa de ~1.5GB RAM)"

# ffmpeg
ffmpeg -version 2>/dev/null | head -1 && echo "  ffmpeg: OK" || echo "  ffmpeg: ⚠️ (necessário para Whisper)"

echo ""
echo "========================================="
echo "  ✅ Instalação concluída!"
echo "========================================="
echo ""
echo "Para iniciar o servidor:"
echo "  cd $BACKEND_DIR"
echo "  python3 main.py"
echo ""
echo "Ou com porta customizada:"
echo "  PORT=8080 python3 main.py"
echo ""
echo "Acesse: http://localhost:8080"
echo ""
echo "Para STT no servidor (opcional):"
echo "  pip install openai-whisper"
echo "  (precisa de ~1.5GB RAM livre e ffmpeg)"
echo ""
echo "Para LLM com API:"
echo "  1. Crie conta em https://openrouter.ai (grátis)"
echo "  2. Gere uma API Key"
echo "  3. Configure no app (ícone ⚙️)"
echo ""
