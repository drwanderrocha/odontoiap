-- ============================================================
-- Schema do Banco de Dados — OdontoAI
-- Versão: 1.0
-- Data: 12/06/2026
-- Compatível: SQLite 3.x / PostgreSQL 15+
-- ============================================================

-- ============================================================
-- 1. PROFISSIONAIS (Dentistas / Equipe)
-- ============================================================
CREATE TABLE IF NOT EXISTS profissionais (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT NOT NULL,
    apelido         TEXT,
    cro             TEXT UNIQUE,              -- Conselho Regional de Odontologia
    cro_uf          TEXT,                     -- UF do CRO (BA, SP, etc.)
    cpf             TEXT UNIQUE,
    email           TEXT UNIQUE,
    celular         TEXT,
    senha_hash      TEXT NOT NULL,            -- bcrypt hash
    cargo           TEXT DEFAULT 'dentista',  -- dentista, secretaria, admin
    nivel_acesso    TEXT DEFAULT 'basico',    -- basico, completo, admin
    ativo           INTEGER DEFAULT 1,        -- 0=inativo, 1=ativo
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- 2. PACIENTES
-- ============================================================
CREATE TABLE IF NOT EXISTS pacientes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT NOT NULL,
    apelido         TEXT,
    data_nascimento TEXT,                     -- ISO 8601: YYYY-MM-DD
    sexo            TEXT CHECK(sexo IN ('M', 'F', 'O')),
    cpf             TEXT UNIQUE,
    rg              TEXT,
    estado_civil    TEXT CHECK(estado_civil IN (
                        'solteiro', 'casado', 'divorciado',
                        'viuvo', 'uniao_estavel', 'nao_informado'
                    )),
    escolaridade    TEXT,
    profissao       TEXT,
    email           TEXT,
    celular         TEXT,
    fone_fixo       TEXT,
    
    -- Endereço (JSON para flexibilidade)
    endereco        TEXT,                     -- JSON: {logradouro, numero, complemento, bairro, cidade, uf, cep}
    
    -- Origem
    como_conheceu   TEXT,                     -- indicacao, google, instagram, whatsapp, outro
    
    -- Dados de saúde geral
    tipo_sanguineo  TEXT,
    observacoes     TEXT,
    
    -- Status
    status          TEXT DEFAULT 'ativo' CHECK(status IN ('ativo', 'inativo')),
    
    -- Metadados
    criado_por      INTEGER REFERENCES profissionais(id),
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

-- Índices para busca rápida
CREATE INDEX IF NOT EXISTS idx_pacientes_nome ON pacientes(nome);
CREATE INDEX IF NOT EXISTS idx_pacientes_cpf ON pacientes(cpf);
CREATE INDEX IF NOT EXISTS idx_pacientes_celular ON pacientes(celular);
CREATE INDEX IF NOT EXISTS idx_pacientes_status ON pacientes(status);

-- ============================================================
-- 3. ANAMNESES
-- ============================================================
CREATE TABLE IF NOT EXISTS anamneses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    
    -- Modo de preenchimento
    modo            TEXT DEFAULT 'profissional' CHECK(modo IN ('paciente', 'profissional')),
    
    -- Respostas (JSON flexível)
    respostas       TEXT NOT NULL DEFAULT '{}',
    -- Exemplo de estrutura JSON:
    -- {
    --   "motivo_consulta": "Dor de dente",
    --   "ultimo_tratamento": "Há 2 anos",
    --   "tratamento_medico": {"resposta": "Sim", "detalhes": "Hipertensão"},
    --   "medicamentos": {"resposta": "Sim", "detalhes": "Losartana 50mg"},
    --   "alergias": {"resposta": "Não", "detalhes": ""},
    --   "reacao_anestesia": {"resposta": "Não", "detalhes": ""},
    --   "gestante": {"resposta": "Não", "detalhes": ""},
    --   "doencas": {"resposta": "Sim", "detalhes": "Diabetes tipo 2"},
    --   "cirurgias": {"resposta": "Não", "detalhes": ""},
    --   "fumante": {"resposta": "Não", "detalhes": ""},
    --   "observacoes_internas": "Paciente ansioso"
    -- }
    
    -- Alertas (perguntas marcadas como alerta)
    alertas         TEXT DEFAULT '[]',       -- JSON array de IDs de perguntas
    
    -- Assinatura
    assinatura_paciente TEXT,                 -- Base64 da assinatura
    assinatura_em   TEXT,                     -- Timestamp da assinatura
    
    -- Observações
    observacoes     TEXT,
    
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_anamneses_paciente ON anamneses(paciente_id);
CREATE INDEX IF NOT EXISTS idx_anamneses_data ON anamneses(criado_em);

-- ============================================================
-- 4. ODONTOGRAMAS
-- ============================================================
CREATE TABLE IF NOT EXISTS odontogramas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    prontuario_id   INTEGER REFERENCES prontuarios(id),
    
    tipo_denticao   TEXT DEFAULT 'permanente' CHECK(tipo_denticao IN ('permanente', 'mista', 'decidua')),
    
    -- Dentes (JSON com todos os 32 dentes permanentes)
    dentes          TEXT NOT NULL DEFAULT '{}',
    -- Exemplo de estrutura JSON:
    -- {
    --   "11": {
    --     "vestibular": {"procedimento": "restauracao", "status": "executado", "data": "2026-01-15"},
    --     "oclusal": null,
    --     "palatina": null,
    --     "lingual": null,
    --     "raiz": {"procedimento": "canal", "status": "a_realizar", "data": null}
    --   },
    --   "16": {
    --     "vestibular": {"procedimento": "coroa", "status": "existente", "data": "2025-06-01"},
    --     ...
    --   }
    -- }
    
    -- Legenda de status
    -- a_realizar: procedimento planejado
    -- executado: procedimento realizado
    -- existente: condição preexistente
    
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_odontogramas_paciente ON odontogramas(paciente_id);

-- ============================================================
-- 5. PRONTUÁRIOS (Fichas Clínicas)
-- ============================================================
CREATE TABLE IF NOT EXISTS prontuarios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    anamnese_id     INTEGER REFERENCES anamneses(id),
    odontograma_id  INTEGER REFERENCES odontogramas(id),
    
    data_consulta   TEXT NOT NULL,            -- ISO 8601: YYYY-MM-DD HH:MM
    
    -- Motivo e diagnóstico
    motivo_consulta TEXT,
    diagnostico     TEXT,
    cid             TEXT,                     -- CID-10 (Classificação Internacional de Doenças)
    
    -- Plano de tratamento
    plano_tratamento TEXT,                    -- Texto livre ou JSON estruturado
    
    -- Procedimentos realizados nesta consulta
    procedimentos   TEXT DEFAULT '[]',
    -- JSON array:
    -- [
    --   {"dente": "25", "face": "oclusal", "procedimento": "restauracao_composta", "material": "resina"},
    --   {"dente": "36", "face": "vestibular", "procedimento": "profilaxia", "material": null}
    -- ]
    
    -- Evolução / Anotações clínicas
    evolucao        TEXT,
    
    -- Prescrições
    prescricoes     TEXT DEFAULT '[]',
    -- JSON array:
    -- [
    --   {"medicamento": "Amoxicilina", "posologia": "500mg 8/8h por 7dias"},
    --   {"medicamento": "Ibuprofeno", "posologia": "400mg se dor"}
    -- ]
    
    -- Atestado / Declarações
    atestado        TEXT,
    
    -- Retorno
    retorno_data    TEXT,                     -- Data sugerida para retorno
    retorno_motivo  TEXT,
    
    -- Observações
    observacoes     TEXT,
    
    -- Metadados
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_prontuarios_paciente ON prontuarios(paciente_id);
CREATE INDEX IF NOT EXISTS idx_prontuarios_profissional ON prontuarios(profissional_id);
CREATE INDEX IF NOT EXISTS idx_prontuarios_data ON prontuarios(data_consulta);

-- ============================================================
-- 6. AGENDA (Consultas Agendadas)
-- ============================================================
CREATE TABLE IF NOT EXISTS agenda (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    
    data_hora_inicio TEXT NOT NULL,           -- ISO 8601: YYYY-MM-DD HH:MM
    data_hora_fim   TEXT,                     -- ISO 8601: YYYY-MM-DD HH:MM
    
    tipo            TEXT DEFAULT 'consulta' CHECK(tipo IN (
                        'consulta', 'retorno', 'procedimento',
                        'avaliacao', 'emergencia', 'limpeza'
                    )),
    
    status          TEXT DEFAULT 'agendado' CHECK(status IN (
                        'agendado', 'confirmado', 'cancelado',
                        'realizado', 'no_show', 'reagendado'
                    )),
    
    -- Confirmação
    confirmacao_enviada_em    TEXT,           -- Quando o WhatsApp foi enviado
    confirmacao_recebida_em   TEXT,           -- Quando o paciente confirmou
    confirmacao_metodo        TEXT,           -- whatsapp, telefone, presencial
    
    -- Retorno (gerado automaticamente após consulta)
    eh_retorno    INTEGER DEFAULT 0,          -- 1 se é retorno de consulta anterior
    consulta_origem_id INTEGER,               -- ID da consulta que gerou este retorno
    
    observacoes     TEXT,
    
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_agenda_paciente ON agenda(paciente_id);
CREATE INDEX IF NOT EXISTS idx_agenda_profissional ON agenda(profissional_id);
CREATE INDEX IF NOT EXISTS idx_agenda_data ON agenda(data_hora_inicio);
CREATE INDEX IF NOT EXISTS idx_agenda_status ON agenda(status);

-- ============================================================
-- 7. ALERTAS DE RETORNO
-- ============================================================
CREATE TABLE IF NOT EXISTS alertas_retorno (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    prontuario_id   INTEGER REFERENCES prontuarios(id),
    
    data_sugerida   TEXT NOT NULL,            -- Data sugerida para retorno
    periodo         TEXT,                     -- "1 semana", "1 mês", "3 meses", etc.
    motivo          TEXT,
    
    status          TEXT DEFAULT 'pendente' CHECK(status IN (
                        'pendente', 'agendado', 'realizado', 'cancelado', 'ignorado'
                    )),
    
    -- Comunicação
    whatsapp_enviado_em   TEXT,
    whatsapp_recebido_em  TEXT,
    
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_alertas_paciente ON alertas_retorno(paciente_id);
CREATE INDEX IF NOT EXISTS idx_alertas_status ON alertas_retorno(status);
CREATE INDEX IF NOT EXISTS idx_alertas_data ON alertas_retorno(data_sugerida);

-- ============================================================
-- 8. FINANCEIRO
-- ============================================================
CREATE TABLE IF NOT EXISTS financeiro (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER REFERENCES pacientes(id),
    prontuario_id   INTEGER REFERENCES prontuarios(id),
    orcamento_id    INTEGER REFERENCES orcamentos(id),
    
    tipo            TEXT NOT NULL CHECK(tipo IN ('receita', 'despesa')),
    categoria       TEXT NOT NULL,
    -- Receitas: consulta, procedimento, protese, ortodontia, implante, outro
    -- Despesas: material, laboratorio, aluguel, salario, imposto, outro
    
    descricao       TEXT NOT NULL,
    valor           REAL NOT NULL,            -- Valor em R$
    
    -- Pagamento
    forma_pagamento TEXT CHECK(forma_pagamento IN (
                        'dinheiro', 'pix', 'cartao_credito', 'cartao_debito',
                        'boleto', 'transferencia', 'cheque', 'convenio'
                    )),
    parcelas        INTEGER DEFAULT 1,
    numero_parcela  INTEGER DEFAULT 1,        -- 1 de 3, 2 de 3, etc.
    
    -- Datas
    data_vencimento TEXT NOT NULL,
    data_pagamento  TEXT,
    
    status          TEXT DEFAULT 'pendente' CHECK(status IN (
                        'pendente', 'pago', 'atrasado', 'cancelado', 'parcial'
                    )),
    
    -- Conciliação
    conciliado      INTEGER DEFAULT 0,
    conciliado_em   TEXT,
    
    observacoes     TEXT,
    
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_financeiro_paciente ON financeiro(paciente_id);
CREATE INDEX IF NOT EXISTS idx_financeiro_tipo ON financeiro(tipo);
CREATE INDEX IF NOT EXISTS idx_financeiro_status ON financeiro(status);
CREATE INDEX IF NOT EXISTS idx_financeiro_vencimento ON financeiro(data_vencimento);

-- ============================================================
-- 9. ORÇAMENTOS
-- ============================================================
CREATE TABLE IF NOT EXISTS orcamentos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    
    -- Itens do orçamento
    itens           TEXT NOT NULL DEFAULT '[]',
    -- JSON array:
    -- [
    --   {"dente": "16", "procedimento": "implante", "valor": 3500.00, "quantidade": 1},
    --   {"dente": "16", "procedimento": "protese_sobre_implante", "valor": 2000.00, "quantidade": 1}
    -- ]
    
    valor_total     REAL NOT NULL,
    
    -- Desconto / Acréscimo
    desconto        REAL DEFAULT 0,
    desconto_tipo   TEXT CHECK(desconto_tipo IN ('percentual', 'valor')),
    valor_final     REAL NOT NULL,
    
    -- Condições de pagamento
    forma_pagamento TEXT,
    parcelas        INTEGER DEFAULT 1,
    
    -- Status
    status          TEXT DEFAULT 'pendente' CHECK(status IN (
                        'pendente', 'aprovado', 'recusado', 'parcial', 'expirado'
                    )),
    
    -- Aprovação
    aprovado_em     TEXT,
    aprovado_por    TEXT,                     -- paciente, responsavel
    
    -- Validade
    validade        TEXT,                     -- Data de validade do orçamento
    
    observacoes     TEXT,
    
    criado_em       TEXT DEFAULT (datetime('now')),
    atualizado_em   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_orcamentos_paciente ON orcamentos(paciente_id);
CREATE INDEX IF NOT EXISTS idx_orcamentos_status ON orcamentos(status);

-- ============================================================
-- 10. DOCUMENTOS (Uploads)
-- ============================================================
CREATE TABLE IF NOT EXISTS documentos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
    prontuario_id   INTEGER REFERENCES prontuarios(id),
    
    tipo            TEXT NOT NULL CHECK(tipo IN (
                        'foto_clinica', 'radiografia', 'tomografia',
                        'atestado', 'receita', 'termo_consentimento',
                        'orcamento_assinado', 'exame_laboratorial',
                        'documento_pessoal', 'outro'
                    )),
    
    nome_arquivo    TEXT NOT NULL,
    caminho         TEXT NOT NULL,            -- Caminho no sistema de arquivos
    tamanho_bytes   INTEGER,
    mime_type       TEXT,
    
    -- Metadados
    descricao       TEXT,
    data_documento  TEXT,                     -- Data do documento (não do upload)
    
    -- Assinatura (se aplicável)
    assinado        INTEGER DEFAULT 0,
    assinatura      TEXT,                     -- Base64
    assinado_em     TEXT,
    
    criado_por      INTEGER REFERENCES profissionais(id),
    criado_em       TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_documentos_paciente ON documentos(paciente_id);
CREATE INDEX IF NOT EXISTS idx_documentos_tipo ON documentos(tipo);

-- ============================================================
-- 11. CONVERSAÇÃO (Histórico de chat com IA)
-- ============================================================
CREATE TABLE IF NOT EXISTS conversas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    paciente_id     INTEGER REFERENCES pacientes(id),  -- Opcional (se for sobre um paciente)
    
    -- Mensagem
    papel           TEXT NOT NULL CHECK(papel IN ('user', 'assistant', 'system')),
    conteudo        TEXT NOT NULL,
    
    -- Metadados da IA
    modelo          TEXT,                     -- Modelo usado (ex: openrouter/owl-alpha)
    tokens_entrada  INTEGER,
    tokens_saida    INTEGER,
    
    -- RAG
    fontes_rag      TEXT DEFAULT '[]',        -- JSON array de fontes usadas
    -- [{"livro": "Manual de Endodontia", "pagina": 45, "trecho": "..."}]
    
    -- Contexto
    contexto        TEXT,                     -- JSON com contexto da conversa
    
    criado_em       TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_conversas_profissional ON conversas(profissional_id);
CREATE INDEX IF NOT EXISTS idx_conversas_paciente ON conversas(paciente_id);
CREATE INDEX IF NOT EXISTS idx_conversas_data ON conversas(criado_em);

-- ============================================================
-- 12. CONFIGURAÇÕES DO SISTEMA
-- ============================================================
CREATE TABLE IF NOT EXISTS configuracoes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profissional_id INTEGER REFERENCES profissionais(id),
    
    chave           TEXT NOT NULL,
    valor           TEXT NOT NULL,
    tipo            TEXT DEFAULT 'string' CHECK(tipo IN ('string', 'number', 'boolean', 'json')),
    
    UNIQUE(profissional_id, chave)
);

-- ============================================================
-- 13. LOGS DE AUDITORIA (LGPD)
-- ============================================================
CREATE TABLE IF NOT EXISTS auditoria (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profissional_id INTEGER REFERENCES profissionais(id),
    
    acao            TEXT NOT NULL,            -- CREATE, READ, UPDATE, DELETE, EXPORT, LOGIN, LOGOUT
    tabela          TEXT NOT NULL,            -- Nome da tabela afetada
    registro_id     INTEGER,                  -- ID do registro afetado
    dados_anteriores TEXT,                    -- JSON (para UPDATE/DELETE)
    dados_novos     TEXT,                     -- JSON (para CREATE/UPDATE)
    
    ip              TEXT,
    user_agent      TEXT,
    
    criado_em       TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_auditoria_profissional ON auditoria(profissional_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_tabela ON auditoria(tabela);
CREATE INDEX IF NOT EXISTS idx_auditoria_data ON auditoria(criado_em);

-- ============================================================
-- 14. TOKENS DE SESSÃO
-- ============================================================
CREATE TABLE IF NOT EXISTS sessoes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profissional_id INTEGER NOT NULL REFERENCES profissionais(id),
    
    token           TEXT NOT NULL UNIQUE,
    expira_em       TEXT NOT NULL,
    
    ip              TEXT,
    user_agent      TEXT,
    
    ativo           INTEGER DEFAULT 1,
    
    criado_em       TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_sessoes_token ON sessoes(token);
CREATE INDEX IF NOT EXISTS idx_sessoes_profissional ON sessoes(profissional_id);

-- ============================================================
-- VIEWS ÚTEIS
-- ============================================================

-- View: Pacientes com última consulta
CREATE VIEW IF NOT EXISTS v_pacientes_ultima_consulta AS
SELECT
    p.*,
    MAX(pr.data_consulta) AS ultima_consulta,
    COUNT(pr.id) AS total_consultas
FROM pacientes p
LEFT JOIN prontuarios pr ON pr.paciente_id = p.id
GROUP BY p.id;

-- View: Agenda do dia
CREATE VIEW IF NOT EXISTS v_agenda_hoje AS
SELECT
    a.*,
    p.nome AS paciente_nome,
    p.celular AS paciente_celular,
    pr.nome AS profissional_nome
FROM agenda a
JOIN pacientes p ON p.id = a.paciente_id
JOIN profissionais pr ON pr.id = a.profissional_id
WHERE date(a.data_hora_inicio) = date('now')
ORDER BY a.data_hora_inicio;

-- View: Financeiro mensal
CREATE VIEW IF NOT EXISTS v_financeiro_mensal AS
SELECT
    strftime('%Y-%m', data_vencimento) AS mes,
    tipo,
    categoria,
    SUM(valor) AS total,
    COUNT(*) AS quantidade
FROM financeiro
WHERE status != 'cancelado'
GROUP BY strftime('%Y-%m', data_vencimento), tipo, categoria
ORDER BY mes DESC;

-- View: Alertas de retorno pendentes
CREATE VIEW IF NOT EXISTS v_alertas_pendentes AS
SELECT
    ar.*,
    p.nome AS paciente_nome,
    p.celular AS paciente_celular
FROM alertas_retorno ar
JOIN pacientes p ON p.id = ar.paciente_id
WHERE ar.status = 'pendente'
ORDER BY ar.data_sugerida;

-- ============================================================
-- DADOS INICIAIS
-- ============================================================

-- Profissional admin padrão (senha: admin123 — trocar em produção!)
-- Hash bcrypt para 'admin123': $2b$12$LJ3m4ys3Lk0TSwMCfNBP0OQDMwEMY5HJKz0a0hxqGKvQ9h9XxYbOi
INSERT OR IGNORE INTO profissionais (nome, cro, email, senha_hash, cargo, nivel_acesso)
VALUES ('Dr. Wander Rocha', 'BA-12345', 'wander@odontoiap.com', '$2b$12$LJ3m4ys3Lk0TSwMCfNBP0OQDMwEMY5HJKz0a0hxqGKvQ9h9XxYbOi', 'admin', 'admin');

-- Configurações padrão
INSERT OR IGNORE INTO configuracoes (chave, valor, tipo) VALUES
('clinica_nome', 'Minha Clínica', 'string'),
('clinica_telefone', '', 'string'),
('clinica_endereco', '', 'string'),
('whatsapp_api_url', '', 'string'),
('whatsapp_api_token', '', 'string'),
('alerta_retorno_dias', '7', 'number'),
('moeda', 'BRL', 'string'),
('timezone', 'America/Bahia', 'string'),
('lgpd_termo_consentimento', 'Eu autorizo o tratamento dos meus dados pessoais para fins de atendimento odontológico, conforme a Lei Geral de Proteção de Dados (LGPD).', 'string');

-- ============================================================
-- NOTAS DE MIGRAÇÃO SQLITE → POSTGRESQL
-- ============================================================
-- 1. INTEGER PRIMARY KEY AUTOINCREMENT → SERIAL PRIMARY KEY
-- 2. TEXT DEFAULT (datetime('now')) → TIMESTAMP DEFAULT NOW()
-- 3. INTEGER (boolean) → BOOLEAN
-- 4. REAL → NUMERIC(10,2)
-- 5. CHECK constraints: manter (PostgreSQL suporta)
-- 6. JSON fields: TEXT → JSONB (melhor performance)
-- 7. Criar ENUMs para campos com CHECK
-- 8. Adicionar schemas: odonto.*
-- ============================================================
