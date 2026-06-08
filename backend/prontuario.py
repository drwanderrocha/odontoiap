"""
OdontoAI — Módulo de Prontuário Odontológico
Templates e extração de entidades para preenchimento por voz.
"""
import re
from dataclasses import dataclass, field
from typing import Optional

# ========== NOMENCLATURA DENTÁRIA ==========
# FDI (Fédération Dentaire Internationale) - sistema de numeração universal

DENTES_PERMANENTES = {
    # Quadrante 1 (superior direito)
    18: "Terceiro molar superior direito", 17: "Segundo molar superior direito",
    16: "Primeiro molar superior direito", 15: "Segundo pré-molar superior direito",
    14: "Primeiro pré-molar superior direito", 13: "Canino superior direito",
    12: "Incisivo lateral superior direito", 11: "Incisivo central superior direito",
    # Quadrante 2 (superior esquerdo)
    21: "Incisivo central superior esquerdo", 22: "Incisivo lateral superior esquerdo",
    23: "Canino superior esquerdo", 24: "Primeiro pré-molar superior esquerdo",
    25: "Segundo pré-molar superior esquerdo", 26: "Primeiro molar superior esquerdo",
    27: "Segundo molar superior esquerdo", 28: "Terceiro molar superior esquerdo",
    # Quadrante 3 (inferior esquerdo)
    38: "Terceiro molar inferior esquerdo", 37: "Segundo molar inferior esquerdo",
    36: "Primeiro molar inferior esquerdo", 35: "Segundo pré-molar inferior esquerdo",
    34: "Primeiro pré-molar inferior esquerdo", 33: "Canino inferior esquerdo",
    32: "Incisivo lateral inferior esquerdo", 31: "Incisivo central inferior esquerdo",
    # Quadrante 4 (inferior direito)
    41: "Incisivo central inferior direito", 42: "Incisivo lateral inferior direito",
    43: "Canino inferior direito", 44: "Primeiro pré-molar inferior direito",
    45: "Segundo pré-molar inferior direito", 46: "Primeiro molar inferior direito",
    47: "Segundo molar inferior direito", 48: "Terceiro molar inferior direito",
}

DENTES_DECÍDUOS = {
    55: "Segundo molar decíduo superior direito", 54: "Primeiro molar decíduo superior direito",
    53: "Canino decíduo superior direito", 52: "Incisivo lateral decíduo superior direito",
    51: "Incisivo central decíduo superior direito",
    61: "Incisivo central decíduo superior esquerdo", 62: "Incisivo lateral decíduo superior esquerdo",
    63: "Canino decíduo superior esquerdo", 64: "Primeiro molar decíduo superior esquerdo",
    65: "Segundo molar decíduo superior esquerdo",
    75: "Segundo molar decíduo inferior esquerdo", 74: "Primeiro molar decíduo inferior esquerdo",
    73: "Canino decíduo inferior esquerdo", 72: "Incisivo lateral decíduo inferior esquerdo",
    71: "Incisivo central decíduo inferior esquerdo",
    81: "Incisivo central decíduo inferior direito", 82: "Incisivo lateral decíduo inferior direito",
    83: "Canino decíduo inferior direito", 84: "Primeiro molar decíduo inferior direito",
    85: "Segundo molar decíduo inferior direito",
}

FACES_DENTARIAS = {
    "mesial": "Mesial", "distal": "Distal",
    "vestibular": "Vestibular", "bucal": "Vestibular",
    "lingual": "Lingual", "palatina": "Palatina", "palatino": "Palatina",
    "oclusal": "Oclusal", "incisal": "Incisal", "o": "Oclusal",
    "v": "Vestibular", "m": "Mesial", "d": "Distal", "l": "Lingual",
    "p": "Palatina",
}

MATERIAIS_RESTAURACAO = {
    "resina composta": "Resina Composta", "resina": "Resina Composta",
    "amálgama": "Amálgama", "amalgama": "Amálgama",
    "ionômero": "Iômero de Vidro", "ionomero": "Iômero de Vidro",
    "iv": "Iômero de Vidro", "compômero": "Compômero",
    "cerômero": "Cerômero", "porcelana": "Porcelama",
    "cerâmica": "Cerâmica", "ceramica": "Cerâmica",
    "ouro": "Ouro", "metálico": "Metálico",
}

PROCEDIMENTOS_ODONTOLOGICOS = {
    "restauração": "Restauração", "restauracao": "Restauração",
    "obturação": "Obturação", "obturacao": "Obturação",
    "extração": "Extração", "extracao": "Extração",
    "exodontia": "Exodontia", "raspagem": "Raspagem",
    "profilaxia": "Profilaxia", "limpeza": "Profilaxia",
    "tratamento de canal": "Tratamento Endodôntico",
    "canal": "Tratamento Endodôntico", "endodontia": "Tratamento Endodôntico",
    "coroa": "Prótese Coroa", "prótese": "Prótese",
    "implante": "Implante", "aparelho": "Aparelho Ortodôntico",
    "extração de siso": "Extração de Terceiro Molar",
    "siso": "Terceiro Molar", "clareamento": "Clareamento Dental",
    "biópsia": "Biópsia", "biopsia": "Biópsia",
    "selante": "Selante", "fluoretação": "Fluoretação",
    "fluor": "Aplicação de Flúor",
}

CLASSIFICACAO_ANGLE = {
    "classe i": "Classe I de Angle (Neutroclusão)",
    "classe 1": "Classe I de Angle (Neutroclusão)",
    "classe ii": "Classe II de Angle (Distoclusão)",
    "classe 2": "Classe II de Angle (Distoclusão)",
    "classe ii divisão 1": "Classe II, Divisão 1 de Angle",
    "classe ii divisão 2": "Classe II, Divisão 2 de Angle",
    "classe iii": "Classe III de Angle (Mesioclusão)",
    "classe 3": "Classe III de Angle (Mesioclusão)",
}


@dataclass
class EntidadeProntuario:
    """Entidades extraídas de uma fala de prontuário."""
    dente: Optional[str] = None
    face: Optional[str] = None
    procedimento: Optional[str] = None
    material: Optional[str] = None
    diagnostico: Optional[str] = None
    observacoes: str = ""
    classificacao_angle: Optional[str] = None


@dataclass
class ProntuarioEntry:
    """Entrada de prontuário estruturada."""
    paciente: str = ""
    data: str = ""
    dente: str = ""
    face: str = ""
    procedimento: str = ""
    material: str = ""
    diagnostico: str = ""
    plano_tratamento: str = ""
    observacoes: str = ""
    odontologo: str = ""
    
    def to_text(self) -> str:
        """Converte para texto formatado do prontuário."""
        parts = []
        if self.dente: parts.append(f"Dente: {self.dente}")
        if self.face: parts.append(f"Face: {self.face}")
        if self.procedimento: parts.append(f"Procedimento: {self.procedimento}")
        if self.material: parts.append(f"Material: {self.material}")
        if self.diagnostico: parts.append(f"Diagnóstico: {self.diagnostico}")
        if self.plano_tratamento: parts.append(f"Plano: {self.plano_tratamento}")
        if self.observacoes: parts.append(f"Obs: {self.observacoes}")
        return " | ".join(parts) if parts else "Nenhum dado extraído"


def extrair_entidades(texto: str) -> EntidadeProntuario:
    """Extrai entidades odontológicas de um texto livre."""
    texto_lower = texto.lower()
    entidade = EntidadeProntuario()
    
    # Extrair dente (número FDI)
    # Padrões: "dente 36", "no 36", "36", "dente nº 36"
    padrao_dente = r'(?:dente|nº|no|numero|número|#)\s*(\d{1,2})|(\d{1,2})\s*(?:superior|inferior|direito|esquerdo)'
    matches = re.findall(padrao_dente, texto_lower)
    for m in matches:
        num = m[0] or m[1]
        if num:
            num_int = int(num)
            if num_int in DENTES_PERMANENTES:
                entidade.dente = f"{num} - {DENTES_PERMANENTES[num_int]}"
                break
            elif num_int in DENTES_DECÍDUOS:
                entidade.dente = f"{num} - {DENTES_DECÍDUOS[num_int]}"
                break
    
    # Se não encontrou com contexto, procurar números isolados
    if not entidade.dente:
        numeros = re.findall(r'\b([1-4][1-8]|[5-8][1-5])\b', texto_lower)
        if numeros:
            num_int = int(numeros[0])
            if num_int in DENTES_PERMANENTES:
                entidade.dente = f"{num_int} - {DENTES_PERMANENTES[num_int]}"
    
    # Extrair face
    for chave, valor in FACES_DENTARIAS.items():
        if chave in texto_lower:
            entidade.face = valor
            break
    
    # Extrair procedimento
    for chave, valor in PROCEDIMENTOS_ODONTOLOGICOS.items():
        if chave in texto_lower:
            entidade.procedimento = valor
            break
    
    # Extrair material
    for chave, valor in MATERIAIS_RESTAURACAO.items():
        if chave in texto_lower:
            entidade.material = valor
            break
    
    # Classificação de Angle
    for chave, valor in CLASSIFICACAO_ANGLE.items():
        if chave in texto_lower:
            entidade.classificacao_angle = valor
            break
    
    return entidade


def formatar_prontuario(entidade: EntidadeProntuario) -> str:
    """Formata as entidades extraídas em texto de prontuário."""
    if not any([entidade.dente, entidade.procedimento, entidade.diagnostico]):
        return ""
    
    partes = []
    if entidade.dente:
        partes.append(f"📍 Dente: {entidade.dente}")
    if entidade.face:
        partes.append(f"📐 Face: {entidade.face}")
    if entidade.procedimento:
        partes.append(f"🔧 Procedimento: {entidade.procedimento}")
    if entidade.material:
        partes.append(f"🧪 Material: {entidade.material}")
    if entidade.diagnostico:
        partes.append(f"🔍 Diagnóstico: {entidade.diagnostico}")
    if entidade.classificacao_angle:
        partes.append(f"📊 Classificação: {entidade.classificacao_angle}")
    if entidade.observacoes:
        partes.append(f"📝 Obs: {entidade.observacoes}")
    
    return "\n".join(partes)


# ========== BASE DE CONHECIMENTO RÁPIDA ==========
# Para uso no modo demo (sem RAG completo)

CONHECIMENTO_ODONTO = {
    "lesão periapical": {
        "titulo": "Lesão Periapical — Diagnóstico Diferencial",
        "conteudo": """Os principais diagnósticos diferenciais para lesão radiolúcida periapical incluem:

1️⃣ **Periodontite Apical Crônica** — Mais comum. Associada a necrose pulpar. Radiolucidez circunscrita.

2️⃣ **Granuloma Periapical** — Lesão inflamatória crônica. Geralmente < 1cm. Assintomático.

3️⃣ **Cisto Periapical** — Lesão de desenvolvimento. Geralmente > 1cm. Pode causar expansão óssea.

4️⃣ **Abscesso Apical Crônico** — Processo infeccioso crônico. Pode ter fístula.

5️⃣ **Cisto Dentígero** (raro em periapical) — Associado a dente incluso.

📋 **Exames recomendados:**
- Teste de vitalidade pulpar
- Radiografia periapical (comparativa)
- CBCT (se disponível)
- Punção aspirativa (se suspeita de cisto)

⚠️ O diagnóstico definitivo é histopatológico."""
    },
    "classe iii": {
        "titulo": "Classe III de Angle",
        "conteudo": """**Classe III de Angle (Mesioclusão)**

📊 **Características:**
- Cúspide mesioventral do 1º molar superior oclui DISTAL ao sulco vestibular do 1º molar inferior
- Relação molar mesial
- Perfil facial côncavo (queixo proeminente)
- Possível mordida cruzada anterior

🔍 **Etiologia:**
- Predisposição genética (fator hereditário forte)
- Deficiência de crescimento maxilar
- Excesso de crescimento mandibular
- Fatores ambientais (respiração bucal, hábitos)

💊 **Tratamento:**
- **Crescimento ativo:** Aparelho funcional (Frankel III, Bionator reverso), máscara facial (Delaire)
- **Casos leves:** Camuflagem ortodôntica
- **Casos graves:** Cirurgia ortognática (avanço maxilar e/ou recuo mandibular)
- **Idade ideal:** Interceptação precoce (7-10 anos)"""
    },
    "classe ii": {
        "titulo": "Classe II de Angle",
        "conteudo": """**Classe II de Angle (Distoclusão)**

📊 **Características:**
- Cúspide mesioventral do 1º molar superior oclui MESIAL ao sulco vestibular do 1º molar inferior
- Relação molar distal
- Perfil facial convexo
- Possível sobremordida profunda

🔍 **Divisões:**
- **Div 1:** Incisivos superiores vestibularizados (inclinados para frente)
- **Div 2:** Incisivos superiores lingualizados (inclinados para trás), laterais vestibularizados

💊 **Tratamento:**
- **Crescimento ativo:** Aparelho funcional (Herbst, Twin Block, Bionator)
- **Casos moderados:** Aparelho fixo + elásticos intermaxilares
- **Casos graves:** Cirurgia ortognática
- **Extrações:** Indicadas em casos de severo apinhamento"""
    },
    "restauração resina": {
        "titulo": "Restauração em Resina Composta",
        "conteudo": """**Restauração em Resina Composta — Protocolo**

📋 **Indicações:**
- Classes I, II, III, IV e V
- Fraturas coronárias
- Substituição de restaurações defeituosas
- Fechamento de diastemas

🔧 **Técnica (incremental):**
1. Isolamento do campo (preferencialmente absoluto)
2. Preparo cavitário (mínimamente invasivo)
3. Condicionamento ácido (37% ácido fosfórico, 15-30s)
4. Lavagem e secagem
5. Aplicação do sistema adesivo (camada fina)
6. Inserção incremental (camadas de 2mm)
7. Fotopolimerização (20-40s por camada)
8. Acabamento e polimento
9. Verificação oclusal

⚠️ **Pontos críticos:**
- Controle de umidade é essencial
- Incrementos de no máximo 2mm
- Fotopolimerizador com intensidade adequada (>500mW/cm²)
- Adaptação marginal"""
    },
    "tratamento de canal": {
        "titulo": "Tratamento Endodôntico",
        "conteudo": """**Tratamento Endodôntico — Visão Geral**

📋 **Indicações:**
- Pulpite irreversível
- Necrose pulpar
- Periodontite apical
- Pré-protético (núcleo)

🔧 **Etapas:**
1. Acesso cameral
2. Localização e cateterismo dos canais
3. Preparo químico-mecânico (NaOCl 2.5-5.25%)
4. Medição do comprimento de trabalho (localizador apical + radiografia)
5. Obturação (gutapercha + cimento — técnica de condensação lateral ou termoplastificada)
6. Restauração coronária definitiva

⚠️ **Complicações possíveis:**
- Perfuração radicular
- Fratura de instrumento
- Extrusão de material
- Dor pós-operatória

📊 **Taxa de sucesso:** 85-97% dependendo do caso"""
    },
    "classificação angle": {
        "titulo": "Classificação de Angle",
        "conteudo": """**Classificação de Angle — Máclusa**

Baseada na relação do primeiro molar permanente:

🔹 **Classe I (Neutroclusão):**
- Cúspide mesioventral do 1º MS alinhada ao sulco vestibular do 1º MI
- Relação normal, mas pode haver apinhamento ou mordida aberta

🔹 **Classe II (Distoclusão):**
- 1º MS MESIAL ao normal em relação ao 1º MI
- **Div 1:** Incisivos superiores vestibularizados, sobremordida profunda
- **Div 2:** Incisivos superiores lingualizados, laterais vestibularizados

🔹 **Classe III (Mesioclusão):**
- 1º MS DISTAL ao normal em relação ao 1º MI
- Perfil côncavo, possível mordida cruzada anterior

📏 **Subdivisões:** Cada classe pode ter subdivisões (direita, esquerda, bilateral)"""
    },
    "nomenclatura faces": {
        "titulo": "Faces Dentárias — Nomenclatura",
        "conteudo": """**Faces Dentárias — Terminologia**

📐 **Faces de um dente:**

🔸 **Mesial** — Face voltada para a linha mediana (frente)
🔸 **Distal** — Face oposta à linha mediana (atrás)
🔸 **Vestibular/Bucal** — Face voltada para a bochecha
🔸 **Lingual** — Face voltada para a língua (dentes inferiores)
🔸 **Palatina** — Face voltada para o palato (dentes superiores)
🔸 **Oclusal** — Face de mordida (pré-molares e molares)
🔸 **Incisal** — Bordo de corte (incisivos e caninos)

📋 **Combinações comuns:**
- MOD = Mesial + Oclusal + Distal
- DV = Distal + Vestibular
- ML = Mesial + Lingual
- O = Oclusal (isolada)

🔢 **Numeração FDI:**
- 1º quadrante: Superior Direito (11-18)
- 2º quadrante: Superior Esquerdo (21-28)
- 3º quadrante: Inferior Esquerdo (31-38)
- 4º quadrante: Inferior Direito (41-48)

Ex: 36 = Primeiro molar inferior esquerdo"""
    },
    "arcada dentária": {
        "titulo": "Arcada Dentária — Visão Geral",
        "conteudo": """**Arcada Dentária**

📋 **Dentição Permanente (32 dentes):**
- 8 Incisivos (4 superiores, 4 inferiores)
- 4 Caninos (2 superiores, 2 inferiores)
- 8 Pré-molares (4 superiores, 4 inferiores)
- 12 Molares (6 superiores, 6 inferiores, incluindo 4 sisos)

📋 **Dentição Decídua (20 dentes):**
- 4 Incisivos superiores, 4 inferiores
- 2 Caninos superiores, 2 inferiores
- 4 Molares superiores, 4 inferiores
- (Não há pré-molares na dentição decídua)

🔢 **Notação FDI (dois dígitos):**
- 1º dígito = quadrante (1-4 permanentes, 5-8 decíduos)
- 2º dígito = dente (1-8 a partir do centro)

Exemplos:
- 11 = Incisivo central superior direito
- 36 = Primeiro molar inferior esquerdo
- 75 = Segundo molar decíduo inferior esquerdo"""
    },
}


def buscar_conhecimento(query: str) -> str:
    """Busca conhecimento odontológico por palavras-chave."""
    query_lower = query.lower()
    
    # Buscar por palavras-chave
    for chave, info in CONHECIMENTO_ODONTO.items():
        palavras = chave.split()
        if any(p in query_lower for p in palavras):
            return f"**{info['titulo']}**\n\n{info['conteudo']}"
    
    return ""


def gerar_resposta_demo(messages: list) -> str:
    """Gera respostas demo baseadas em conhecimento local."""
    user_msg = messages[-1]["content"].lower() if messages else ""
    
    # Tentar buscar na base de conhecimento
    conhecimento = buscar_conhecimento(user_msg)
    if conhecimento:
        return conhecimento + "\n\n⚠️ *Esta é uma sugestão baseada em literatura. O diagnóstico definitivo é responsabilidade do profissional.*"
    
    # Respostas para prontuário
    if any(w in user_msg for w in ["prontuário", "prontuario", "registrar", "anotar"]):
        entidade = extrair_entidades(user_msg)
        if entidade.dente or entidade.procedimento:
            formatted = formatar_prontuario(entidade)
            return f"📋 **Registro de Prontuário Extraído:**\n\n{formatted}\n\n✅ Dados extraídos com sucesso! No modo completo, isso seria salvo automaticamente no prontuário do paciente."
        
        return """📋 **Prontuário por Voz**

Para registrar no prontuário, diga algo como:
- *"Restauração em resina composta no 36, face oclusal"*
- *"Extração do dente 48"*
- *"Tratamento de canal no 26"*
- *"Restauração em amálgama no 14, mesio-oclusal"*

Vou extrair automaticamente: dente, face, procedimento e material."""
    
    # Respostas para diagnóstico
    if any(w in user_msg for w in ["diagnóstico", "diagnostico", "diagnosticar"]):
        return """🔍 **Suporte ao Diagnóstico**

Para sugestões de diagnóstico diferencial, me conte:
- Sintomas do paciente
- Achados clínicos
- Achados radiográficos (se houver)

Exemplo: *"Paciente com dor espontânea no 36, sensibilidade ao frio, radiografia mostra lesão periapical"*

⚠️ Lembre-se: sou um assistente. O diagnóstico definitivo é sempre do profissional."""
    
    # Respostas para pacientes
    if any(w in user_msg for w in ["paciente", "retorno", "agendar", "consulta"]):
        return """👥 **Gestão de Pacientes**

No modo completo, posso ajudar com:
- 📅 Agendar consultas e retornos
- 📋 Listar pacientes com retorno atrasado
- 📞 Gerar lembretes automáticos
- 📊 Acompanhamento de tratamentos

Configure uma API Key do OpenRouter para ativar todas as funcionalidades."""
    
    # Respostas para dúvidas gerais
    if any(w in user_msg for w in ["olá", "ola", "oi", "hey", "bom dia", "boa tarde", "boa noite"]):
        return """👋 Olá, Doutor! Sou o **OdontoAI**, seu assistente odontológico.

Posso ajudar com:
- 📋 **Prontuário** — Registrar procedimentos por voz
- 🔍 **Diagnóstico** — Sugestões de diferenciais
- 📚 **Conhecimento** — Dúvidas clínicas
- 👥 **Pacientes** — Gestão e acompanhamento

🎤 Pressione o microfone e fale comigo! Ou digite sua pergunta.

💡 **Dica:** Para respostas mais completas com IA avançada, configure uma API Key gratuita do OpenRouter (ícone ⚙️)."""
    
    # Resposta padrão
    return f"""Entendo sua pergunta sobre: *"{user_msg[:60]}..."*

No modo demo, tenho respostas para:
- 🦷 Diagnósticos diferenciais (ex: lesão periapical)
- 📊 Classificação de Angle (Classes I, II, III)
- 🔧 Procedimentos (restauração, canal, extração)
- 📐 Nomenclatura (faces dentárias, numeração FDI)
- 📋 Registro de prontuário por voz

Para respostas completas com IA avançada, configure uma **API Key gratuita** do OpenRouter nas configurações (⚙️).

Modelos gratuitos recomendados:
- Google Gemini 2.0 Flash (free)
- DeepSeek V3 (free)"""
