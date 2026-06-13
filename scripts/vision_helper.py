#!/usr/bin/env python3
"""
Vision helper - Analisa imagens usando OpenRouter API
Modelo: google/gemma-4-26b-a4b-it:free
Uso: python3 vision_helper.py <caminho_da_imagem> [pergunta]
"""
import base64, json, urllib.request, sys, time
from pathlib import Path

VISION_MODEL = "google/gemma-4-26b-a4b-it:free"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

def get_api_key():
    """Carrega a API key do .env."""
    env_path = Path('/opt/data/.env')
    if env_path.exists():
        for line in env_path.read_text().split('\n'):
            if 'OPENROUTER_API_KEY' in line and '=' in line:
                return line.split('=', 1)[1].strip()
    # Fallback: variável de ambiente
    import os
    return os.environ.get('OPENROUTER_API_KEY', '')

def analyze_image(image_path: str, question: str = "Descreva esta imagem em detalhes.") -> str:
    """Analisa uma imagem usando o modelo de visão do OpenRouter."""
    
    key = get_api_key()
    if not key:
        return "Erro: OPENROUTER_API_KEY não encontrada"
    
    # Carrega imagem
    data = open(image_path, 'rb').read()
    img_b64 = base64.b64encode(data).decode()
    
    # Tenta até 3 vezes (rate limit)
    for attempt in range(3):
        try:
            payload = json.dumps({
                'model': VISION_MODEL,
                'messages': [{
                    'role': 'user',
                    'content': [
                        {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{img_b64}'}},
                        {'type': 'text', 'text': question}
                    ]
                }],
                'max_tokens': 500
            }).encode()

            req = urllib.request.Request(
                f'{OPENROUTER_BASE}/chat/completions',
                data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {key}',
                    'HTTP-Referer': 'https://odontoiap.com',
                    'X-Title': 'OdontoAI'
                },
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                return result['choices'][0]['message']['content']
                
        except urllib.error.HTTPError as e:
            if e.code == 429:
                if attempt < 2:
                    time.sleep(5 * (attempt + 1))
                    continue
                return f"Erro: Rate limit (429). Tente novamente em alguns segundos."
            return f"Erro HTTP {e.code}: {e.reason}"
        except Exception as e:
            return f"Erro: {e}"
    
    return "Erro: Todas as tentativas falharam"

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 vision_helper.py <caminho_da_imagem> [pergunta]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else "Descreva esta imagem em detalhes. Se for um erro, copie o texto exato."
    
    result = analyze_image(image_path, question)
    print(result)
