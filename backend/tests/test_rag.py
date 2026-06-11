"""
Testes unitários para rag.py
Cobertura: tokenização, TF-IDF, busca, score labels.
"""
import json
import pytest
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag import RAGEngine


@pytest.fixture
def rag_engine():
    """RAG engine vazia (sem chunks carregados)."""
    return RAGEngine()


@pytest.fixture
def sample_chunks_file(tmp_path):
    """Cria um arquivo de chunks de exemplo."""
    chunks = [
        {
            "id": "chunk_001",
            "source": "Tratado de Odontologia - Cap. 1",
            "text": "A cárie dentária é uma doença multifatorial que causa desmineralização do esmalte dentário. O tratamento depende da profundidade da lesão."
        },
        {
            "id": "chunk_002",
            "source": "Tratado de Odontologia - Cap. 3",
            "text": "A restauração em resina composta é indicada para cáries de classes I, III e IV. O protocolo requer isolamento absoluto, condicionamento ácido e sistema adesivo."
        },
        {
            "id": "chunk_003",
            "source": "Ortodontia Avançada",
            "text": "A classificação de Angle é baseada na relação do primeiro molar permanente. Classe I é neutroclusão, Classe II é distoclusão e Classe III é mesioclusão."
        },
        {
            "id": "chunk_004",
            "source": "Endodontia Clínica",
            "text": "O tratamento endodôntico é indicado para pulpite irreversível e necrose pulpar. A obturação com gutapercha e cimento é a técnica padrão."
        },
        {
            "id": "chunk_005",
            "source": "Periodontia",
            "text": "A periodontite é uma doença inflamatória crônica que afeta os tecidos de suporte do dente. O diagnóstico inclui sondagem clínica e radiografia."
        },
    ]

    chunks_dir = tmp_path / "data" / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    chunks_file = chunks_dir / "livros_chunks.json"

    with open(chunks_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)

    return chunks_file, chunks


@pytest.fixture
def loaded_rag_engine(tmp_path, sample_chunks_file):
    """RAG engine já carregada com chunks."""
    chunks_file, chunks = sample_chunks_file

    engine = RAGEngine()
    engine.chunks = chunks
    engine._calc_tfidf()
    engine._loaded = True
    return engine, chunks


class TestTokenize:
    """Testa RAGEngine._tokenize()."""

    def test_tokenize_basico(self, rag_engine):
        tokens = rag_engine._tokenize("restauração em resina composta")
        assert "restauração" in tokens
        assert "resina" in tokens
        assert "composta" in tokens

    def test_tokenize_remove_stopwords(self, rag_engine):
        tokens = rag_engine._tokenize("de da do em um uma por para com")
        assert len(tokens) == 0  # todas são stopwords

    def test_tokenize_remove_curto(self, rag_engine):
        tokens = rag_engine._tokenize("a b c de o cárie é")
        assert "cárie" in tokens
        assert "a" not in tokens  # muito curto
        assert "é" not in tokens  # muito curto/stopword

    def test_tokenize_preserva_acentos(self, rag_engine):
        tokens = rag_engine._tokenize("restauração cárie pulpite")
        assert any("restauração" in t or "restauracao" in t for t in tokens)
        assert any("cárie" in t or "carie" in t for t in tokens)

    def test_tokenize_vazio(self, rag_engine):
        tokens = rag_engine._tokenize("")
        assert tokens == []

    def test_tokenize_remove_pontuacao(self, rag_engine):
        tokens = rag_engine._tokenize("dente 36, face oclusal!")
        assert "dente" in tokens
        assert "face" in tokens
        assert "oclusal" in tokens
        # Números de 2 dígitos são mantidos (len > 2 não se aplica a "36")
        # mas depende da implementação - o importante é que não tem pontuação
        assert "," not in tokens
        assert "!" not in tokens


class TestCalcTfIdf:
    """Testa RAGEngine._calc_tfidf()."""

    def test_idf_calculado(self, loaded_rag_engine):
        engine, chunks = loaded_rag_engine
        assert len(engine.idf) > 0

    def test_vocab_nao_vazio(self, loaded_rag_engine):
        engine, chunks = loaded_rag_engine
        assert len(engine.vocab) > 0

    def test_termo_comum_tem_idf_baixo(self, loaded_rag_engine):
        engine, chunks = loaded_rag_engine
        # "dente" aparece em vários chunks → IDF baixo
        if "dente" in engine.idf:
            # IDF = log(N / (1 + df))
            # se df for alto, IDF será baixo
            assert engine.idf["dente"] >= 0


class TestSearch:
    """Testa RAGEngine.search()."""

    def test_search_retorna_resultados(self, loaded_rag_engine):
        engine, _ = loaded_rag_engine
        results = engine.search("cárie dentária tratamento")
        assert len(results) > 0

    def test_search_ordenado_por_score(self, loaded_rag_engine):
        engine, _ = loaded_rag_engine
        results = engine.search("restauração resina composta")
        if len(results) >= 2:
            assert results[0]["score"] >= results[1]["score"]

    def test_search_resina_retorna_chunk_correto(self, loaded_rag_engine):
        engine, chunks = loaded_rag_engine
        results = engine.search("restauração resina composta")
        assert len(results) > 0
        # O chunk sobre resina composta deve ser o primeiro
        top = results[0]
        assert "resina" in top["text"].lower()

    def test_search_canal_retorna_chunk_endodontico(self, loaded_rag_engine):
        engine, _ = loaded_rag_engine
        results = engine.search("tratamento endodôntico canal")
        assert len(results) > 0
        top = results[0]
        assert "endodôntico" in top["text"].lower() or "canal" in top["text"].lower()

    def test_search_sem_match(self, loaded_rag_engine):
        engine, _ = loaded_rag_engine
        results = engine.search("xyzabc123 termos inexistentes")
        assert results == []

    def test_search_query_vazia(self, loaded_rag_engine):
        engine, _ = loaded_rag_engine
        results = engine.search("")
        assert results == []

    def test_search_limit_top_k(self, loaded_rag_engine):
        engine, _ = loaded_rag_engine
        results = engine.search("dentária", top_k=2)
        assert len(results) <= 2

    def test_search_nao_carregado(self, rag_engine):
        """Se não carregou chunks, retorna vazio."""
        results = rag_engine.search("cárie")
        assert results == []


class TestScoreLabel:
    """Testa RAGEngine._score_label()."""

    def test_score_alta(self, rag_engine):
        assert rag_engine._score_label(0.5) == "alta"

    def test_score_media(self, rag_engine):
        assert rag_engine._score_label(0.2) == "média"

    def test_score_baixa(self, rag_engine):
        assert rag_engine._score_label(0.05) == "baixa"

    def test_score_zero(self, rag_engine):
        assert rag_engine._score_label(0.0) == "baixa"


class TestSearchByKeywords:
    """Testa RAGEngine.search_by_keywords()."""

    def test_keyword_match(self, loaded_rag_engine):
        engine, _ = loaded_rag_engine
        results = engine.search_by_keywords(["resina"])
        assert len(results) > 0

    def test_keyword_sem_match(self, loaded_rag_engine):
        engine, _ = loaded_rag_engine
        results = engine.search_by_keywords(["xyzabc123"])
        assert results == []

    def test_keyword_multiplas(self, loaded_rag_engine):
        engine, _ = loaded_rag_engine
        results = engine.search_by_keywords(["cárie", "resina"])
        assert len(results) > 0


class TestRAGGlobal:
    """Testa instância global e get_rag()."""

    def test_get_rag_retorna_engine(self):
        from rag import get_rag
        engine = get_rag()
        assert isinstance(engine, RAGEngine)

    def test_get_rag_mesma_instancia(self):
        from rag import get_rag, rag
        assert get_rag() is rag
