-- ============================================================
-- OdontoAI Schema v3.0 — PostgreSQL / Supabase
-- Execute este SQL no SQL Editor do Supabase
-- ============================================================

-- Habilitar extensão UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. PROFISSIONAIS
-- ============================================================
CREATE TABLE IF NOT EXISTS profissionais (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome            TEXT NOT NULL,
    apelido         TEXT,
    cro             TEXT UNIQUE,
    cro_uf          TEXT,
    cpf             TEXT UNIQUE,
    email           TEXT UNIQUE,
    celular         TEXT,
    senha_hash      TEXT NOT NULL DEFAULT '',
    cargo           TEXT DEFAULT 'dentista',
    nivel_acesso    TEXT DEFAULT 'basico',
    ativo           BOOLEAN DEFAULT true,
    criado_em       TIMESTAMPTZ DEFAULT now(),
    atualizado_em   TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 2. PACIENTES
-- ============================================================
CREATE TABLE IF NOT EXISTS pacientes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profissional_id UUID REFERENCES profissionais(id),
    nome            TEXT NOT NULL,
    apelido         TEXT,
    data_nascimento DATE,
    sexo            TEXT CHECK(sexo IN ('M', 'F', 'O')),
    cpf             TEXT UNIQUE,
    rg              TEXT,
    estado_civil    TEXT,
    escolaridade    TEXT,
    profissao       TEXT,
    email           TEXT,
    celular         TEXT,
    fone_fixo       TEXT,
    endereco        TEXT,
    cidade          TEXT,
    estado          TEXT,
    cep             TEXT,
    como_conheceu   TEXT,
    tipo_sanguineo  TEXT,
    alergias        TEXT,
    medicamentos    TEXT,
    observacoes     TEXT,
    status          TEXT DEFAULT 'ativo',
    criado_em       TIMESTAMPTZ DEFAULT now(),
    atualizado_em   TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pacientes_nome ON pacientes(nome);
CREATE INDEX IF NOT EXISTS idx_pacientes_cpf ON pacientes(cpf);
CREATE INDEX IF NOT EXISTS idx_pacientes_profissional ON pacientes(profissional_id);

-- ============================================================
-- 3. ANAMNESES
-- ============================================================
CREATE TABLE IF NOT EXISTS anamneses (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paciente_id     UUID NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    profissional_id UUID NOT NULL REFERENCES profissionais(id),
    modo            TEXT DEFAULT 'profissional',
    respostas       JSONB NOT NULL DEFAULT '{}',
    alertas         JSONB DEFAULT '[]',
    assinatura_paciente TEXT,
    assinatura_em   TIMESTAMPTZ,
    observacoes     TEXT,
    criado_em       TIMESTAMPTZ DEFAULT now(),
    atualizado_em   TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_anamneses_paciente ON anamneses(paciente_id);

-- ============================================================
-- 4. ODONTOGRAMAS
-- ============================================================
CREATE TABLE IF NOT EXISTS odontogramas (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paciente_id     UUID NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    prontuario_id   UUID,
    tipo_denticao   TEXT DEFAULT 'permanente',
    dentes          JSONB NOT NULL DEFAULT '{}',
    criado_em       TIMESTAMPTZ DEFAULT now(),
    atualizado_em   TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_odontogramas_paciente ON odontogramas(paciente_id);

-- ============================================================
-- 5. PRONTUÁRIOS
-- ============================================================
CREATE TABLE IF NOT EXISTS prontuarios (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paciente_id     UUID NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    profissional_id UUID NOT NULL REFERENCES profissionais(id),
    anamnese_id     UUID REFERENCES anamneses(id),
    odontograma_id  UUID REFERENCES odontogramas(id),
    data_consulta   DATE NOT NULL,
    motivo_consulta TEXT,
    diagnostico     TEXT,
    cid             TEXT,
    plano_tratamento TEXT,
    procedimentos   JSONB DEFAULT '[]',
    evolucao        TEXT,
    prescricoes     JSONB DEFAULT '[]',
    atestado        TEXT,
    retorno_data    DATE,
    retorno_motivo  TEXT,
    observacoes     TEXT,
    criado_em       TIMESTAMPTZ DEFAULT now(),
    atualizado_em   TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_prontuarios_paciente ON prontuarios(paciente_id);
CREATE INDEX IF NOT EXISTS idx_prontuarios_profissional ON prontuarios(profissional_id);
CREATE INDEX IF NOT EXISTS idx_prontuarios_data ON prontuarios(data_consulta);

-- ============================================================
-- 6. AGENDA
-- ============================================================
CREATE TABLE IF NOT EXISTS agenda (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paciente_id     UUID NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    profissional_id UUID NOT NULL REFERENCES profissionais(id),
    data_hora_inicio TIMESTAMPTZ NOT NULL,
    data_hora_fim   TIMESTAMPTZ,
    tipo            TEXT DEFAULT 'consulta',
    status          TEXT DEFAULT 'agendado',
    confirmacao_enviada_em   TIMESTAMPTZ,
    confirmacao_recebida_em  TIMESTAMPTZ,
    confirmacao_metodo       TEXT,
    eh_retorno               BOOLEAN DEFAULT false,
    consulta_origem_id       UUID,
    observacoes     TEXT,
    criado_em       TIMESTAMPTZ DEFAULT now(),
    atualizado_em   TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agenda_paciente ON agenda(paciente_id);
CREATE INDEX IF NOT EXISTS idx_agenda_profissional ON agenda(profissional_id);
CREATE INDEX IF NOT EXISTS idx_agenda_data ON agenda(data_hora_inicio);

-- ============================================================
-- 7. ALERTAS DE RETORNO
-- ============================================================
CREATE TABLE IF NOT EXISTS alertas_retorno (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paciente_id     UUID NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    prontuario_id   UUID REFERENCES prontuarios(id),
    data_sugerida   DATE NOT NULL,
    periodo         TEXT,
    motivo          TEXT,
    status          TEXT DEFAULT 'pendente',
    whatsapp_enviado_em   TIMESTAMPTZ,
    whatsapp_recebido_em  TIMESTAMPTZ,
    criado_em       TIMESTAMPTZ DEFAULT now(),
    atualizado_em   TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_alertas_paciente ON alertas_retorno(paciente_id);
CREATE INDEX IF NOT EXISTS idx_alertas_status ON alertas_retorno(status);

-- ============================================================
-- 8. ORÇAMENTOS
-- ============================================================
CREATE TABLE IF NOT EXISTS orcamentos (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paciente_id     UUID NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    profissional_id UUID NOT NULL REFERENCES profissionais(id),
    itens           JSONB NOT NULL DEFAULT '[]',
    valor_total     NUMERIC(10,2) NOT NULL,
    desconto        NUMERIC(10,2) DEFAULT 0,
    desconto_tipo   TEXT,
    valor_final     NUMERIC(10,2) NOT NULL,
    forma_pagamento TEXT,
    parcelas        INTEGER DEFAULT 1,
    status          TEXT DEFAULT 'pendente',
    aprovado_em     TIMESTAMPTZ,
    aprovado_por    TEXT,
    validade        DATE,
    observacoes     TEXT,
    criado_em       TIMESTAMPTZ DEFAULT now(),
    atualizado_em   TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_orcamentos_paciente ON orcamentos(paciente_id);
CREATE INDEX IF NOT EXISTS idx_orcamentos_status ON orcamentos(status);

-- ============================================================
-- 9. FINANCEIRO
-- ============================================================
CREATE TABLE IF NOT EXISTS financeiro (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paciente_id     UUID REFERENCES pacientes(id),
    prontuario_id   UUID REFERENCES prontuarios(id),
    orcamento_id    UUID REFERENCES orcamentos(id),
    tipo            TEXT NOT NULL CHECK(tipo IN ('receita', 'despesa')),
    categoria       TEXT NOT NULL,
    descricao       TEXT NOT NULL,
    valor           NUMERIC(10,2) NOT NULL,
    forma_pagamento TEXT,
    parcelas        INTEGER DEFAULT 1,
    numero_parcela  INTEGER DEFAULT 1,
    data_vencimento DATE NOT NULL,
    data_pagamento  DATE,
    status          TEXT DEFAULT 'pendente',
    conciliado      BOOLEAN DEFAULT false,
    conciliado_em   TIMESTAMPTZ,
    observacoes     TEXT,
    criado_em       TIMESTAMPTZ DEFAULT now(),
    atualizado_em   TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_financeiro_paciente ON financeiro(paciente_id);
CREATE INDEX IF NOT EXISTS idx_financeiro_tipo ON financeiro(tipo);
CREATE INDEX IF NOT EXISTS idx_financeiro_status ON financeiro(status);

-- ============================================================
-- 10. DOCUMENTOS
-- ============================================================
CREATE TABLE IF NOT EXISTS documentos (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paciente_id     UUID NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    prontuario_id   UUID REFERENCES prontuarios(id),
    tipo            TEXT NOT NULL,
    nome_arquivo    TEXT NOT NULL,
    storage_path    TEXT NOT NULL,
    tamanho_bytes   INTEGER,
    mime_type       TEXT,
    descricao       TEXT,
    data_documento  DATE,
    assinado        BOOLEAN DEFAULT false,
    assinatura      TEXT,
    assinado_em     TIMESTAMPTZ,
    criado_por      UUID REFERENCES profissionais(id),
    criado_em       TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_documentos_paciente ON documentos(paciente_id);

-- ============================================================
-- 11. CONVERSAS
-- ============================================================
CREATE TABLE IF NOT EXISTS conversas (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profissional_id UUID NOT NULL REFERENCES profissionais(id),
    paciente_id     UUID REFERENCES pacientes(id),
    papel           TEXT NOT NULL CHECK(papel IN ('user', 'assistant', 'system')),
    conteudo        TEXT NOT NULL,
    modelo          TEXT,
    tokens_entrada  INTEGER,
    tokens_saida    INTEGER,
    fontes_rag      JSONB DEFAULT '[]',
    contexto        JSONB,
    criado_em       TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_conversas_profissional ON conversas(profissional_id);
CREATE INDEX IF NOT EXISTS idx_conversas_paciente ON conversas(paciente_id);

-- ============================================================
-- 12. CONFIGURAÇÕES
-- ============================================================
CREATE TABLE IF NOT EXISTS configuracoes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profissional_id UUID REFERENCES profissionais(id),
    chave           TEXT NOT NULL,
    valor           TEXT NOT NULL,
    tipo            TEXT DEFAULT 'string',
    UNIQUE(profissional_id, chave)
);

-- ============================================================
-- 13. AUDITORIA
-- ============================================================
CREATE TABLE IF NOT EXISTS auditoria (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profissional_id UUID REFERENCES profissionais(id),
    acao            TEXT NOT NULL,
    tabela          TEXT NOT NULL,
    registro_id     UUID,
    dados_anteriores JSONB,
    dados_novos     JSONB,
    ip              INET,
    user_agent      TEXT,
    criado_em       TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_auditoria_profissional ON auditoria(profissional_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_tabela ON auditoria(tabela);

-- ============================================================
-- 14. SESSÕES
-- ============================================================
CREATE TABLE IF NOT EXISTS sessoes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profissional_id UUID NOT NULL REFERENCES profissionais(id),
    token           TEXT NOT NULL UNIQUE,
    expira_em       TIMESTAMPTZ NOT NULL,
    ip              INET,
    user_agent      TEXT,
    ativo           BOOLEAN DEFAULT true,
    criado_em       TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sessoes_token ON sessoes(token);

-- ============================================================
-- STORAGE BUCKET
-- ============================================================
INSERT INTO storage.buckets (id, name, public) 
VALUES ('documentos', 'documentos', false)
ON CONFLICT (id) DO NOTHING;
