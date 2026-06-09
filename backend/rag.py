#!/usr/bin/env python3
"""
OdontoAI — RAG Search Engine
Busca semântica nos livros odontológicos usando TF-IDF + fallback para ChromaDB.
"""
import json
import re
from pathlib import Path
from collections import Counter
import math

DATA_DIR = Path(__file__).parent.parent / "data"
CHUNKS_FILE = DATA_DIR / "chunks" / "livros_chunks.json"

class RAGEngine:
    """Motor de busca RAG com TF-IDF."""
    
    def __init__(self):
        self.chunks = []
        self.tf_idf = {}
        self.idf = {}
        self.vocab = set()
        self._loaded = False
    
    def load(self):
        """Carrega chunks e calcula TF-IDF."""
        if self._loaded:
            return
        
        if not CHUNKS_FILE.exists():
            print("⚠️ Chunks não encontrados. Rodar process_rag.py primeiro.")
            return
        
        with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
            self.chunks = json.load(f)
        
        # Calcular TF-IDF
        self._calc_tfidf()
        self._loaded = True
        print(f"✅ RAG Engine carregado: {len(self.chunks)} chunks")
    
    def _tokenize(self, text: str) -> list[str]:
        """Tokeniza texto em português."""
        text = text.lower()
        # Manter acentos, remover pontuação
        text = re.sub(r'[^\w\s\-]', ' ', text)
        tokens = text.split()
        # Stopwords PT-BR básicas
        stopwords = {'de', 'da', 'do', 'dos', 'das', 'em', 'um', 'uma', 'no', 'na',
                     'nos', 'nas', 'por', 'para', 'com', 'sem', 'sobre', 'até',
                     'que', 'se', 'ao', 'aos', 'ou', 'mais', 'mas', 'como', 'são',
                     'foi', 'ser', 'ter', 'está', 'tem', 'seu', 'sua', 'seus', 'suas',
                     'este', 'esta', 'esse', 'essa', 'aquele', 'aquela'}
        return [t for t in tokens if len(t) > 2 and t not in stopwords]
    
    def _calc_tfidf(self):
        """Calcula TF-IDF para todos os chunks."""
        if not self.chunks:
            return
        
        # Calcular DF (document frequency)
        df = Counter()
        for chunk in self.chunks:
            tokens = set(self._tokenize(chunk['text']))
            for token in tokens:
                df[token] += 1
        
        # Calcular IDF
        n_docs = len(self.chunks)
        self.idf = {token: math.log(n_docs / (1 + freq)) for token, freq in df.items()}
        
        # Vocabulário
        self.vocab = set(df.keys())
    
    def _calc_chunk_tf(self, text: str) -> dict:
        """Calcula TF de um texto."""
        tokens = self._tokenize(text)
        tf = Counter(tokens)
        total = len(tokens) if tokens else 1
        return {token: count / total for token, count in tf.items()}
    
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Busca os chunks mais relevantes usando TF-IDF."""
        if not self._loaded:
            return []
        
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        
        scores = []
        for i, chunk in enumerate(self.chunks):
            chunk_tf = self._calc_chunk_tf(chunk['text'])
            score = 0
            for token in query_tokens:
                if token in chunk_tf and token in self.idf:
                    score += chunk_tf[token] * self.idf[token]
            if score > 0:
                scores.append((i, score))
        
        # Ordenar por score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in scores[:top_k]:
            chunk = self.chunks[idx]
            results.append({
                "id": chunk['id'],
                "source": chunk['source'],
                "text": chunk['text'][:500],  # Limite de chars
                "score": round(score, 4),
                "relevance": self._score_label(score)
            })
        
        return results
    
    def _score_label(self, score: float) -> str:
        if score > 0.3:
            return "alta"
        elif score > 0.1:
            return "média"
        return "baixa"
    
    def search_by_keywords(self, keywords: list[str], top_k: int = 5) -> list[dict]:
        """Busca por palavras-chave específicas (fallback)."""
        if not self._loaded:
            return []
        
        pattern = re.compile('|'.join(re.escape(k) for k in keywords), re.IGNORECASE)
        
        scored = []
        for chunk in self.chunks:
            matches = pattern.findall(chunk['text'])
            if matches:
                score = len(matches) / (len(chunk['text']) / 100)  # matches por 100 chars
                scored.append((chunk, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [{
            "id": c['id'],
            "source": c['source'],
            "text": c['text'][:500],
            "score": round(s, 4),
            "relevance": "alta" if s > 0.5 else "média" if s > 0.2 else "baixa"
        } for c, s in scored[:top_k]]

# Instância global
rag = RAGEngine()

def get_rag() -> RAGEngine:
    """Retorna instância do RAG engine."""
    return rag
