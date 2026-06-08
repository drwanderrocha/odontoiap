# 🦷 OdontoAI — Assistente Odontológico com IA

> Assistente de IA voice-first para dentistas brasileiros. PWA + RAG odontológico.

## ✨ Funcionalidades

- 🎤 **Prontuário por Voz** — Registre procedimentos, diagnósticos e observações falando com o agente
- 🔍 **Suporte ao Diagnóstico** — Sugestões de diagnósticos diferenciais baseados em literatura
- 📚 **Base de Conhecimento (RAG)** — Respostas fundamentadas em livros, artigos e diretrizes de odontologia
- 📋 **Gestão de Pacientes** — Acompanhamento, retornos e lembretes
- 📱 **PWA** — App instalável no celular, funciona offline
- 🔊 **Voz** — Conversação natural por voz (STT + TTS em PT-BR)

## 🖥️ Screenshot

*Em desenvolvimento*

## 🚀 Stack Tecnológica

| Camada | Tecnologia | Custo |
|--------|-----------|-------|
| Frontend | PWA (HTML/JS/CSS) | Gratuito |
| Backend | FastAPI (Python) | Open-source |
| STT | Web Speech API (navegador) | Gratuito |
| TTS | edge-tts (Microsoft) | Gratuito |
| LLM | OpenRouter (free tier) | Gratuito |
| Deploy | VPS + Ngrok | ~$70/mês |

## 📦 Instalação

### Pré-requisitos
- Python 3.11+
- FFmpeg
- Conta no OpenRouter (opcional, para LLM avançado)

### Setup

```bash
# Clone o repositório
git clone https://github.com/drwanderrocha/odontoiap.git
cd odontoiap

# Instale as dependências e inicie
chmod +x install.sh
./install.sh

# Rode o servidor
cd backend
python3 main.py
```

O servidor iniciará em `http://localhost:8080`

### Com Nginx (produção)

```bash
# Configure o nginx como reverse proxy
# Exemplo de configuração em /etc/nginx/sites-available/

server {
    listen 80;
    server_name _;

    location /odonto/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 300;
        proxy_buffering off;
    }
}
```

## 🔧 Configuração

### API Key do OpenRouter (opcional)

Para respostas LLM mais avançadas, configure uma API Key gratuita:

1. Crie conta em [openrouter.ai](https://openrouter.ai)
2. Gere uma API Key em [openrouter.ai/keys](https://openrouter.ai/keys)
3. Configure no app (ícone ⚙️)

Modelos gratuitos recomendados:
- `google/gemini-2.0-flash-exp:free`
- `deepseek/deepseek-chat-v3-0324:free`
- `qwen/qwen-2.5-72b-instruct:free`

## 📡 API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/health` | Health check |
| POST | `/api/chat` | Chat por texto |
| POST | `/api/voice` | Chat por voz (recebe áudio) |
| POST | `/api/prontuario/extrair` | Extrai entidades de prontuário |
| POST | `/api/prontuario/conhecimento` | Busca conhecimento odontológico |
| GET | `/audio/{filename}` | Arquivos de áudio TTS |

## 📁 Estrutura do Projeto

```
odontoiap/
├── backend/
│   ├── main.py          # FastAPI server + endpoints
│   ├── prontuario.py    # Extração de entidades + base de conhecimento
│   └── requirements.txt # Dependências Python
├── frontend/
│   ├── index.html       # PWA completa (chat, voz, UI)
│   ├── manifest.json    # PWA manifest
│   ├── sw.js            # Service Worker
│   └── static/          # Ícones e assets
├── audio_cache/         # Áudios TTS gerados
├── install.sh           # Script de instalação
├── .gitignore
└── README.md
```

## ⚠️ Aviso Importante

Este software é um **assistente clínico**. Ele **NÃO substitui** o profissional dentista. Todas as sugestões devem ser revisadas e aprovadas pelo profissional responsável. O diagnóstico e plano de tratamento são sempre de responsabilidade do dentista.

## 📄 Licença

MIT License

## 👨‍💻 Autor

**Wander Rocha** ([@drwanderrocha](https://github.com/drwanderrocha))

---

*Desenvolvido com ❤️ para a comunidade odontológica brasileira.*
