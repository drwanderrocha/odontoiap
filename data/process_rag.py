#!/usr/bin/env python3
"""
OdontoAI — RAG Pipeline
Processa livros odontológicos e cria índice de busca vetorial.
"""
import os
import re
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent
LIVROS_DIR = DATA_DIR / "livros"
CHUNKS_DIR = DATA_DIR / "chunks"
CHUNKS_DIR.mkdir(exist_ok=True)

CHUNK_SIZE = 1000  # caracteres por chunk
CHUNK_OVERLAP = 200  # overlap entre chunks

def clean_text(text: str) -> str:
    """Limpa texto extraído de PDF/MD."""
    # Remover headers markdown repetidos
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remover linhas vazias excessivas
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remover caracteres especiais mas manter acentos
    text = re.sub(r'[^\w\s\-\.\,\;\:\!\?\(\)\/\%\°]', ' ', text)
    # Remover espaços múltiplos
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()

def chunk_text(text: str, source: str) -> list[dict]:
    """Divide texto em chunks com overlap."""
    chunks = []
    start = 0
    chunk_id = 0
    
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]
        
        # Tentar quebrar em parágrafo ou frase
        if end < len(text):
            # Procurar última quebra de parágrafo
            last_para = chunk.rfind('\n\n')
            if last_para > CHUNK_SIZE * 0.5:
                end = start + last_para
                chunk = text[start:end]
            else:
                # Procurar último ponto
                last_period = chunk.rfind('. ')
                if last_period > CHUNK_SIZE * 0.5:
                    end = start + last_period + 1
                    chunk = text[start:end]
        
        chunk = chunk.strip()
        if len(chunk) > 100:  # Ignorar chunks muito pequenos
            chunks.append({
                "id": f"{source}_{chunk_id:04d}",
                "source": source,
                "text": chunk,
                "start": start,
                "end": end,
                "length": len(chunk)
            })
            chunk_id += 1
        
        start = end - CHUNK_OVERLAP
    
    return chunks

def process_file(filepath: Path) -> list[dict]:
    """Processa um arquivo de livro."""
    print(f"📖 {filepath.name}...")
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    
    text = clean_text(text)
    source = filepath.stem.replace('.md', '').replace('.txt', '')
    chunks = chunk_text(text, source)
    
    print(f"   → {len(chunks)} chunks")
    return chunks

def main():
    print("🦷 OdontoAI — RAG Pipeline")
    print("=" * 50)
    
    all_chunks = []
    
    # Processar todos os arquivos
    for ext in ['*.md', '*.txt']:
        for filepath in sorted(LIVROS_DIR.glob(ext)):
            chunks = process_file(filepath)
            all_chunks.extend(chunks)
    
    # Salvar chunks
    chunks_file = CHUNKS_DIR / "livros_chunks.json"
    with open(chunks_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    
    # Criar índice de texto simples (para busca sem embeddings)
    index_file = CHUNKS_DIR / "livros_index.txt"
    with open(index_file, 'w', encoding='utf-8') as f:
        for chunk in all_chunks:
            f.write(f"[{chunk['source']}]\n{chunk['text']}\n\n{'='*80}\n\n")
    
    # Estatísticas
    print()
    print("=" * 50)
    print(f"✅ Processamento completo!")
    print(f"   Arquivos: {len(list(LIVROS_DIR.glob('*')))}")
    print(f"   Chunks totais: {len(all_chunks)}")
    print(f"   Tamanho médio: {sum(c['length'] for c in all_chunks) // len(all_chunks)} chars")
    print(f"   Arquivo de chunks: {chunks_file}")
    
    # Salvar metadados
    metadata = {
        "total_chunks": len(all_chunks),
        "sources": list(set(c['source'] for c in all_chunks)),
        "chunk_size": CHUNK_SIZE,
        "overlap": CHUNK_OVERLAP,
        "files_processed": len(list(LIVROS_DIR.glob('*')))
    }
    
    with open(CHUNKS_DIR / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

if __name__ == "__main__":
    main()
