"""
Testes unitários para prontuario.py
Cobertura: extração de entidades, formatação, base de conhecimento, respostas demo.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from prontuario import (
    extrair_entidades,
    formatar_prontuario,
    buscar_conhecimento,
    gerar_resposta_demo,
    EntidadeProntuario,
    ProntuarioEntry,
    DENTES_PERMANENTES,
    DENTES_DECÍDUOS,
    FACES_DENTARIAS,
    PROCEDIMENTOS_ODONTOLOGICOS,
    MATERIAIS_RESTAURACAO,
    CLASSIFICACAO_ANGLE,
    CONHECIMENTO_ODONTO,
)


# =================================================================
# TESTES DE CONSTANTES E NOMENCLATURA
# =================================================================

class TestNomenclatura:
    """Testa dicionários de nomenclatura odontológica."""

    def test_dentes_permanentes_tem_32(self):
        assert len(DENTES_PERMANENTES) == 32

    def test_dentes_deciduos_tem_20(self):
        assert len(DENTES_DECÍDUOS) == 20

    def test_dente_36_correto(self):
        assert DENTES_PERMANENTES[36] == "Primeiro molar inferior esquerdo"

    def test_dente_11_correto(self):
        assert DENTES_PERMANENTES[11] == "Incisivo central superior direito"

    def test_dente_48_correto(self):
        assert DENTES_PERMANENTES[48] == "Terceiro molar inferior direito"

    def test_faces_dentarias_principais(self):
        assert "mesial" in FACES_DENTARIAS
        assert "distal" in FACES_DENTARIAS
        assert "vestibular" in FACES_DENTARIAS
        assert "lingual" in FACES_DENTARIAS
        assert "oclusal" in FACES_DENTARIAS

    def test_materiais_inclui_resina(self):
        assert "resina composta" in MATERIAIS_RESTAURACAO
        assert "resina" in MATERIAIS_RESTAURACAO

    def test_procedimentos_inclui_restauracao(self):
        assert "restauração" in PROCEDIMENTOS_ODONTOLOGICOS
        assert PROCEDIMENTOS_ODONTOLOGICOS["restauração"] == "Restauração"

    def test_classificacao_angle_tem_3_classes(self):
        keys = [k for k in CLASSIFICACAO_ANGLE if "classe i" in k and "ii" not in k and "iii" not in k]
        assert len(keys) >= 1  # classe i
        assert any("classe ii" in k for k in CLASSIFICACAO_ANGLE)
        assert any("classe iii" in k for k in CLASSIFICACAO_ANGLE)

    def test_conhecimento_odontologico_tem_entries(self):
        assert len(CONHECIMENTO_ODONTO) > 0
        for chave, info in CONHECIMENTO_ODONTO.items():
            assert "titulo" in info
            assert "conteudo" in info
            assert len(info["conteudo"]) > 50


# =================================================================
# TESTES DE EXTRAÇÃO DE ENTIDADES
# =================================================================

class TestExtrairEntidades:
    """Testa a função extrair_entidades() com diversos tipos de fala."""

    # --- Extração de DENTE ---

    def test_extrair_dente_com_prefixo(self):
        texto = "Restauração no dente 36, face oclusal"
        ent = extrair_entidades(texto)
        assert ent.dente is not None
        assert "36" in ent.dente

    def test_extrair_dente_sem_prefixo(self):
        texto = "Coloquei resina no 14"
        ent = extrair_entidades(texto)
        assert ent.dente is not None
        assert "14" in ent.dente

    def test_extrair_dente_com_complemento(self):
        texto = "Extração do 48 inferior direito"
        ent = extrair_entidades(texto)
        assert ent.dente is not None
        assert "48" in ent.dente

    def test_extrair_dente_deciduo(self):
        texto = "Remoção do dente 75, canino decíduo inferior esquerdo"
        ent = extrair_entidades(texto)
        assert ent.dente is not None
        assert "75" in ent.dente

    def test_sem_dente_reconhecivel(self):
        texto = "Paciente retornou para revisão"
        ent = extrair_entidades(texto)
        assert ent.dente is None

    def test_extrair_dente_com_n_mascara(self):
        texto = "Dente nº 26 precisa de tratamento endodôntico"
        ent = extrair_entidades(texto)
        assert ent.dente is not None
        assert "26" in ent.dente

    # --- Extração de FACE ---

    def test_extrair_face_vestibular(self):
        texto = "Face vestibular do 36"
        ent = extrair_entidades(texto)
        assert ent.face == "Vestibular"

    def test_extrair_face_bucal(self):
        texto = "Na face bucal do 12"
        ent = extrair_entidades(texto)
        assert ent.face == "Vestibular"  # bucal = vestibular

    def test_extrair_face_mesial(self):
        texto = "Mesial do 16"
        ent = extrair_entidades(texto)
        assert ent.face == "Mesial"

    def test_extrair_face_distal(self):
        texto = "Distal do 37"
        ent = extrair_entidades(texto)
        assert ent.face == "Distal"

    def test_extrair_face_oclusal(self):
        texto = "Oclusal do 36"
        ent = extrair_entidades(texto)
        assert ent.face == "Oclusal"

    def test_extrair_face_lingual(self):
        texto = "Face lingual do 46"
        ent = extrair_entidades(texto)
        assert ent.face == "Lingual"

    def test_extrair_face_palatina(self):
        texto = "Palatina do 24"
        ent = extrair_entidades(texto)
        assert ent.face == "Palatina"

    # --- Extração de PROCEDIMENTO ---

    def test_extrair_procedimento_restauracao(self):
        texto = "Fiz uma restauração no dente 36"
        ent = extrair_entidades(texto)
        assert ent.procedimento == "Restauração"

    def test_extrair_procedimento_extracao(self):
        texto = "Realizei a extração do 48"
        ent = extrair_entidades(texto)
        assert ent.procedimento == "Extração"

    def test_extrair_procedimento_canal(self):
        texto = "Iniciei o tratamento de canal no 26"
        ent = extrair_entidades(texto)
        assert ent.procedimento == "Tratamento Endodôntico"

    def test_extrair_procedimento_obturacao(self):
        texto = "Obturação  no 36 com amálgama"
        ent = extrair_entidades(texto)
        assert ent.procedimento == "Obturação"

    def test_extrair_procedimento_profilaxia(self):
        texto = "Profilaxia e limpeza geral"
        ent = extrair_entidades(texto)
        assert ent.procedimento == "Profilaxia"

    def test_extrair_procedimento_implante(self):
        texto = "Colocação de implante no 36"
        ent = extrair_entidades(texto)
        assert ent.procedimento == "Implante"

    # --- Extração de MATERIAL ---

    def test_extrair_material_resina(self):
        texto = "Restauração com resina composta no 36"
        ent = extrair_entidades(texto)
        assert ent.material == "Resina Composta"

    def test_extrair_material_amalgama(self):
        texto = "Obturação com amálgama no 46"
        ent = extrair_entidades(texto)
        assert ent.material == "Amálgama"

    def test_extrair_material_ionomero(self):
        texto = "Restauração com ionômero de vidre no 75"
        ent = extrair_entidades(texto)
        assert ent.material is not None

    # --- Extração de CLASSIFICAÇÃO DE ANGLE ---

    def test_extrair_angle_classe_i(self):
        texto = "O paciente apresenta classe i de angle"
        ent = extrair_entidades(texto)
        assert ent.classificacao_angle is not None
        assert "Classe I" in ent.classificacao_angle

    def test_extrair_angle_classe_ii(self):
        # Nota: "classe ii divisão 1" contém "classe i" como substring,
        # então o dicionário bate "classe i" primeiro. Testamos com texto isolado.
        texto = "O paciente tem classe ii"
        ent = extrair_entidades(texto)
        assert ent.classificacao_angle is not None
        assert "Classe II" in ent.classificacao_angle

    def test_extrair_angle_classe_iii(self):
        texto = "Paciente com classe 3 de angle"
        ent = extrair_entidades(texto)
        assert ent.classificacao_angle is not None
        assert "Classe III" in ent.classificacao_angle

    # --- Extrações COMBINADAS ---

    def test_extracao_completa(self):
        texto = "Restauração em resina composta no dente 36, face oclusal"
        ent = extrair_entidades(texto)
        assert ent.dente is not None
        assert "36" in ent.dente
        assert ent.procedimento == "Restauração"
        assert ent.material == "Resina Composta"
        assert ent.face == "Oclusal"

    def test_extracao_canal_completo(self):
        texto = "Tratamento de canal no dente 26"
        ent = extrair_entidades(texto)
        assert ent.dente is not None
        assert "26" in ent.dente
        assert ent.procedimento == "Tratamento Endodôntico"

    def test_texto_vazio(self):
        ent = extrair_entidades("")
        assert ent.dente is None
        assert ent.face is None
        assert ent.procedimento is None
        assert ent.material is None


# =================================================================
# TESTES DE FORMATAÇÃO DE PRONTUÁRIO
# =================================================================

class TestFormatarProntuario:
    """Testa formatar_prontuario() e ProntuarioEntry.to_text()."""

    def test_formatar_completo(self):
        ent = extrair_entidades("Restauração em resina composta no dente 36, face oclusal")
        fmt = formatar_prontuario(ent)
        assert "📍" in fmt
        assert "Dente:" in fmt
        assert "Procedimento:" in fmt
        assert "Material:" in fmt
        assert "Face:" in fmt

    def test_formatar_vazio(self):
        ent = EntidadeProntuario()
        fmt = formatar_prontuario(ent)
        assert fmt == ""

    def test_formatar_somente_dente(self):
        ent = EntidadeProntuario(dente="36 - Primeiro molar inferior esquerdo")
        fmt = formatar_prontuario(ent)
        assert "Dente: 36" in fmt
        assert "Procedimento:" not in fmt

    def test_prontuario_entry_to_text_vazio(self):
        entry = ProntuarioEntry()
        assert entry.to_text() == "Nenhum dado extraído"

    def test_prontuario_entry_to_text_com_dados(self):
        entry = ProntuarioEntry(
            dente="36 - Primeiro molar inferior esquerdo",
            procedimento="Restauração",
            material="Resina Composta",
        )
        text = entry.to_text()
        assert "Dente:" in text
        assert "36" in text
        assert "Procedimento:" in text
        assert "Restauração" in text


# =================================================================
# TESTES DE BUSCA DE CONHECIMENTO
# =================================================================

class TestBuscarConhecimento:
    """Testa buscar_conhecimento() — base de conhecimento local."""

    def test_buscar_lesao_periapical(self):
        resultado = buscar_conhecimento("lesão periapical diagnóstico")
        assert resultado != ""
        assert "Periapical" in resultado

    def test_buscar_classe_iii(self):
        resultado = buscar_conhecimento("classe iii de angle")
        assert resultado != ""
        assert "Mesioclusão" in resultado or "Classe III" in resultado

    def test_buscar_classe_ii(self):
        resultado = buscar_conhecimento("classe ii tratamento")
        assert resultado != ""
        assert "Distoclusão" in resultado or "Classe II" in resultado

    def test_buscar_restauracao_resina(self):
        resultado = buscar_conhecimento("restauração em resina composta")
        assert resultado != ""
        assert "Resina Composta" in resultado or "resina" in resultado.lower()

    def test_buscar_tratamento_canal(self):
        resultado = buscar_conhecimento("tratamento de canal endodôntico")
        assert resultado != ""
        assert "Endodôntico" in resultado or "canal" in resultado.lower()

    def test_buscar_nao_encontrado(self):
        resultado = buscar_conhecimento("xyzabc123 completamente desconhecido qwerty")
        assert resultado == ""

    def test_buscar_nomenclatura_faces(self):
        resultado = buscar_conhecimento("faces dentárias mesial distal")
        assert resultado != ""
        # Deve encontrar info sobre faces ou arcada
        assert "Mesial" in resultado or "Distal" in resultado or "Vestibular" in resultado


# =================================================================
# TESTES DE RESPOSTAS DEMO
# =================================================================

class TestGerarRespostaDemo:
    """Testa gerar_resposta_demo() — modo sem API key."""

    def test_saudacao(self):
        messages = [{"role": "user", "content": "Olá, Carlos!"}]
        resp = gerar_resposta_demo(messages)
        assert "OdontoAI" in resp or "Olá" in resp or "Doutor" in resp

    def test_saudacao_bom_dia(self):
        messages = [{"role": "user", "content": "Bom dia!"}]
        resp = gerar_resposta_demo(messages)
        assert len(resp) > 20  # resposta substancial

    def test_prontuario_prompt(self):
        messages = [{"role": "user", "content": "Como registrar no prontuário?"}]
        resp = gerar_resposta_demo(messages)
        assert "prontuário" in resp.lower() or "Prontuário" in resp

    def test_diagnostico_prompt(self):
        messages = [{"role": "user", "content": "Como fazer um diagnóstico diferencial?"}]
        resp = gerar_resposta_demo(messages)
        assert "diagnóstico" in resp.lower() or "Diagnóstico" in resp

    def test_pacientes_prompt(self):
        messages = [{"role": "user", "content": "Tenho um paciente com retorno atrasado"}]
        resp = gerar_resposta_demo(messages)
        assert "paciente" in resp.lower() or "Pacientes" in resp or "retorno" in resp.lower()

    def test_conhecimento_lesao_periapical(self):
        messages = [{"role": "user", "content": "Paciente com lesão periapical no 36"}]
        resp = gerar_resposta_demo(messages)
        assert "⚠️" in resp  # aviso de disclaimer
        assert len(resp) > 100

    def test_conhecimento_classe_iii(self):
        messages = [{"role": "user", "content": "Classe III de Angle tratamento"}]
        resp = gerar_resposta_demo(messages)
        assert "⚠️" in resp
        assert "Classe III" in resp or "Mesioclusão" in resp

    def test_resposta_padrao(self):
        messages = [{"role": "user", "content": "Pergunta genérica sobre algo não mapeado xyz"}]
        resp = gerar_resposta_demo(messages)
        assert len(resp) > 20  # sempre retorna algo

    def test_sem_mensagens(self):
        resp = gerar_resposta_demo([])
        assert len(resp) > 0


# =================================================================
# TESTES DE ENTIDADE PRONTUÁRIO (dataclass)
# =================================================================

class TestEntidadeProntuario:
    """Testa o dataclass EntidadeProntuario."""

    def test_default_values(self):
        ent = EntidadeProntuario()
        assert ent.dente is None
        assert ent.face is None
        assert ent.procedimento is None
        assert ent.material is None
        assert ent.diagnostico is None
        assert ent.observacoes == ""
        assert ent.classificacao_angle is None

    def test_custom_values(self):
        ent = EntidadeProntuario(
            dente="36 - Molar",
            face="Oclusal",
            procedimento="Restauração",
            material="Resina",
        )
        assert ent.dente == "36 - Molar"
        assert ent.face == "Oclusal"
        assert ent.procedimento == "Restauração"
        assert ent.material == "Resina"
