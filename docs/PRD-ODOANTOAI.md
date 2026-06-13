# 📋 PRD — OdontoAI

**Versão:** 1.0  
**Data:** 12/06/2026  
**Autor:** Dr. Wander Rocha Carvalho + Carlos (IA)  
**Status:** Em desenvolvimento

---

## 1. Visão Geral

### 1.1 Problema

Dentistas brasileiros enfrentam dificuldades significativas com:
- **Gestão de clínica**: Planilhas, papel, sistemas complexos e caros
- **Prontuário**: Preenchimento manual demorado durante/after consulta
- **Acompanhamento de pacientes**: Falta de follow-up estruturado
- **Decisões clínicas**: Isolamento profissional, sem acesso rápido a literatura
- **Tecnologia**: Sistemas existentes são caros (R$150-400/mês) e não são intuitivos

### 1.2 Solução

**OdontoAI** — Um agente de IA que funciona como **parceiro do dentista**, acessível por **voz e texto**, com:
- Conversação natural em português
- Preenchimento automático de prontuário por voz
- RAG (base de conhecimento odontológico) para fundamentar decisões
- CRM de pacientes com alertas de retorno
- Gestão financeira simplificada
- PWA (sem instalação) — funciona no celular

### 1.3 Diferencial Competitivo

| Aspecto | Clinicorp | OdontoAI |
|---------|-----------|----------|
| Interface principal | Visual/manual | **Voz-first** |
| IA | Gestão/vendas | **Copiloto clínico** |
| Base de conhecimento | Não tem | **RAG com 19+ livros** |
| Custo | R$150-400/mês | **Gratuito/open source** |
| Instalação | App + web | **PWA (só acessar)** |
| Preenchimento prontuário | Manual | **Por voz** |
| Análise de caso | Não tem | **IA sugere diagnóstico/plano** |
| Público | Clínicas médias/grandes | **Dentista solo + clínicas** |

---

## 2. Personas

### 2.1 Persona Primária: Dr. Wander (Dentista Solo)
- **Idade:** 35-50 anos
- **Consultório:** 1-2 cadeiras, 1 secretária
- **Tech-savvy:** Médio (usa WhatsApp, Instagram, Google)
- **Dores:** Perde tempo com papel, esquece de follow-up, quer agilizar atendimento
- **Objetivo:** Atender mais pacientes com menos burocracia

### 2.2 Persona Secundária: Dra. Andreza (Clínica Pequena)
- **Idade:** 30-45 anos
- **Clínica:** 3-5 dentistas, equipe de recepção
- **Tech-savvy:** Baixo (equipe tem dificuldade com sistemas)
- **Dores:** Organização, controle financeiro, retenção de pacientes
- **Objetivo:** Profissionalizar a gestão sem gastar muito

### 2.3 Persona Terciária: Paciente
- **Perfil:** Adulto que precisa de tratamento odontológico
- **Necessidade:** Ser lembrado de retornos, ter acesso ao plano de tratamento
- **Canal:** WhatsApp (principal), app do paciente (secundário)

---

## 3. Funcionalidades

### 3.1 Módulo 1: Agente Conversacional (MVP - Fase 1)

**Descrição:** Interface principal do dentista com o sistema — uma IA que entende e responde em português.

**Funcionalidades:**
- [ ] Chat por texto com IA (RAG odontológico)
- [ ] Chat por voz com IA (STT + TTS)
- [ ] Respostas baseadas em literatura odontológica (19 livros)
- [ ] Sugestão de diagnóstico e plano de tratamento
- [ ] Discussão de casos clínicos ("como se fosse um colega")

**Critérios de Aceite:**
- Resposta em < 10 segundos
- Transcrição de voz com > 90% de precisão (português)
- Respostas fundamentadas com citação da fonte

### 3.2 Módulo 2: Gestão de Pacientes (CRM) (Fase 1)

**Descrição:** Cadastro e acompanhamento de pacientes.

**Funcionalidades:**
- [ ] Cadastro completo (dados pessoais, contato, saúde)
- [ ] Lista de pacientes com busca
- [ ] Status (ativo/inativo)
- [ ] Histórico de consultas
- [ ] Alertas de retorno automáticos
- [ ] Confirmação de retorno via WhatsApp

**Modelo de Dados:**
```
Paciente
├── id (PK)
├── nome
├── apelido
├── data_nascimento
├── sexo
├── cpf
├── rg
├── estado_civil
├── escolaridade
├── email
├── celular
├── fone_fixo
├── endereco (JSON)
├── como_conheceu
├── observacoes
├── status (ativo/inativo)
├── criado_em
└── atualizado_em
```

### 3.3 Módulo 3: Prontuário Digital (Fase 2)

**Descrição:** Prontuário eletrônico preenchido por voz e/ou manualmente.

**Funcionalidades:**
- [ ] Anamnese estruturada (perguntas padrão + personalizadas)
- [ ] Anamnese por voz (dentista fala, sistema preenche)
- [ ] Ficha clínica por especialidade
- [ ] Assinatura eletrônica do paciente
- [ ] Histórico de evolução
- [ ] Alertas de saúde (alergias, medicamentos, condições)

**Modelo de Dados:**
```
Prontuario
├── id (PK)
├── paciente_id (FK)
├── profissional_id (FK)
├── data_consulta
├── motivo_consulta
├── anamnese (JSON)
├── diagnostico
├── plano_tratamento
├── procedimentos_realizados (JSON)
├── observacoes
├── alertas (JSON)
├── assinatura_paciente (base64)
├── criado_em
└── atualizado_em
```

### 3.4 Módulo 4: Odontograma (Fase 2)

**Descrição:** Representação visual da arcada dentária com marcação de procedimentos.

**Funcionalidades:**
- [ ] SVG interativo (32 dentes permanentes)
- [ ] Faces: Vestibular, Oclusal, Palatina, Lingual
- [ ] Legenda: A realizar, Executado, Existente
- [ ] Marcador por voz ("restauração no 16 vestibular")
- [ ] Histórico de alterações
- [ ] Dentição: Permanente/Mista/Decídua

**Modelo de Dados:**
```
Odontograma
├── id (PK)
├── paciente_id (FK)
├── prontuario_id (FK)
├── dentição (permanente/mista/decídua)
├── dentes (JSON) → [{numero, face, procedimento, status, data}]
├── criado_em
└── atualizado_em
```

### 3.5 Módulo 5: Agenda (Fase 3)

**Descrição:** Gerenciamento de consultas e compromissos.

**Funcionalidades:**
- [ ] Calendário semanal/mensal
- [ ] Agendamento por voz ("agendar Rita para quinta às 14h")
- [ ] Confirmação automática via WhatsApp
- [ ] Alerta de retorno automático
- [ ] Bloqueio de horários
- [ ] Múltiplos profissionais

**Modelo de Dados:**
```
Agenda
├── id (PK)
├── paciente_id (FK)
├── profissional_id (FK)
├── data_hora_inicio
├── data_hora_fim
├── tipo (consulta/retorno/procedimento)
├── status (agendado/confirmado/cancelado/realizado)
├── observacoes
├── criado_em
└── atualizado_em
```

### 3.6 Módulo 6: Gestão Financeira (Fase 3)

**Descrição:** Controle financeiro simplificado da clínica.

**Funcionalidades:**
- [ ] Registro de receitas e despesas
- [ ] Orçamentos por paciente
- [ ] Pagamentos (parcelado/à vista)
- [ ] Relatórios mensais
- [ ] Integração com maquininha (futuro)

**Modelo de Dados:**
```
Financeiro
├── id (PK)
├── paciente_id (FK)
├── prontuario_id (FK)
├── tipo (receita/despesa)
├── categoria
├── valor
├── forma_pagamento
├── parcelas
├── data_vencimento
├── data_pagamento
├── status (pendente/pago/atrasado)
├── observacoes
├── criado_em
└── atualizado_em
```

### 3.7 Módulo 7: App do Paciente (Fase 4)

**Descrição:** PWA para o paciente acompanhar seu tratamento.

**Funcionalidades:**
- [ ] Visualizar plano de tratamento
- [ ] Ver próximas consultas
- [ ] Confirmar presença via WhatsApp
- [ ] Receber lembretes de retorno
- [ ] Acessar documentos (receitas, atestados)
- [ ] Ver odontograma (visualização)

### 3.8 Módulo 8: Relatórios e Dashboard (Fase 4)

**Descrição:** Visão analítica da clínica.

**Funcionalidades:**
- [ ] Dashboard com métricas principais
- [ ] Pacientes ativos/inativos
- [ ] Faturamento mensal
- [ ] Taxa de retorno
- [ ] Procedimentos mais realizados
- [ ] Relatórios exportáveis (PDF/CSV)

---

## 4. Arquitetura Técnica

### 4.1 Stack

```
Frontend:
├── PWA (HTML5 + CSS3 + JavaScript)
├── Service Worker (offline-first)
├── WebSocket (voz em tempo real)
└── Responsivo (mobile-first)

Backend:
├── Python 3.12 + FastAPI
├── SQLite (desenvolvimento) → PostgreSQL (produção)
├── ChromaDB (RAG - vetores)
├── faster-whisper (STT - transcrição)
├── edge-tts (TTS - síntese de voz)
└── OpenRouter API (LLM - conversação)

Infraestrutura:
├── VPS Hostiger (Docker)
├── ngrok (tunnel público)
└── GitHub (backup automático)
```

### 4.2 Fluxo de Voz

```
1. Dentista fala → Microfone do celular
2. Áudio (WebM) → WebSocket → Servidor
3. WebM → WAV (ffmpeg)
4. WAV → faster-whisper → Texto (português)
5. Texto + contexto → RAG (ChromaDB) → Contexto relevante
6. Texto + contexto → LLM (OpenRouter) → Resposta
7. Resposta → edge-tts → Áudio (MP3)
8. Áudio → WebSocket → Celular do dentista
9. Resposta → Prontuário (se aplicável)
```

### 4.3 Fluxo RAG

```
Base de Conhecimento:
├── 19 livros de odontologia (PDF → texto → chunks)
├── Embeddings (text-embedding-ada-002 ou similar)
├── Armazenados no ChromaDB
└── Busca por similaridade semântica

Query:
├── Pergunta do dentista → Embedding
├── Busca top-K chunks similares
├── Chunks + pergunta → LLM
└── Resposta fundamentada com fonte
```

---

## 5. Roadmap de Implementação

### Fase 1: MVP (Semanas 1-4) — ✅ EM ANDAMENTO
- [x] Backend FastAPI com endpoints básicos
- [x] Chat por texto com RAG
- [x] Chat por voz (WebSocket + whisper + TTS)
- [x] Cadastro de pacientes (CRUD)
- [x] PWA frontend básico
- [x] Testes unitários (152 testes)
- [x] Deploy VPS + ngrok
- [x] Backup GitHub automático
- [ ] Refinar RAG com mais livros
- [ ] Melhorar latência do chat

### Fase 2: Prontuário (Semanas 5-8)
- [ ] Anamnese estruturada
- [ ] Anamnese por voz
- [ ] Odontograma SVG interativo
- [ ] Ficha clínica por especialidade
- [ ] Assinatura eletrônica
- [ ] Histórico de evolução

### Fase 3: Gestão (Semanas 9-12)
- [ ] Agenda com calendário
- [ ] Agendamento por voz
- [ ] Confirmação via WhatsApp
- [ ] Alertas de retorno
- [ ] Gestão financeira básica
- [ ] Orçamentos

### Fase 4: Paciente + Analytics (Semanas 13-16)
- [ ] App do paciente (PWA)
- [ ] Dashboard financeiro
- [ ] Relatórios
- [ ] Métricas de retenção
- [ ] Exportação de dados

### Fase 5: IA Avançada (Semanas 17-20)
- [ ] Análise de fotos clínicas (visão)
- [ ] Sugestão automática de diagnóstico
- [ ] Planos de tratamento gerados por IA
- [ ] Análise de radiografias (futuro)
- [ ] Integração com laboratórios

---

## 6. Requisitos Não-Funcionais

### 6.1 Performance
- Resposta do chat: < 10 segundos
- Transcrição de voz: < 5 segundos
- Carregamento do PWA: < 3 segundos
- Suporte a 50+ pacientes sem degradação

### 6.2 Segurança
- Dados de pacientes criptografados (LGPD)
- Autenticação JWT
- HTTPS obrigatório
- Backup diário automático
- Logs de auditoria

### 6.3 Disponibilidade
- PWA funciona offline (cache)
- Sincronização quando online
- Uptime 99% (VPS)

### 6.4 Usabilidade
- Interface em português brasileiro
- Voz em português brasileiro
- Mobile-first (celular > desktop)
- Curva de aprendizado < 1 dia

### 6.5 Compatibilidade
- Chrome 90+
- Safari 15+
- Android 10+
- iOS 15+

---

## 7. Métricas de Sucesso

| Métrica | Meta Fase 1 | Meta Fase 2 | Meta Final |
|---------|-------------|-------------|------------|
| Precisão STT (PT-BR) | 85% | 90% | 95% |
| Satisfação do dentista | 7/10 | 8/10 | 9/10 |
| Tempo de prontuário | - | -50% | -70% |
| Retorno de pacientes | - | +20% | +40% |
| Usuários ativos | 1 (Wander) | 5 | 100+ |

---

## 8. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Whisper com sotaque regional | Média | Alto | Fine-tuning com dados BR |
| Latência da IA | Alta | Médio | Cache + modelos menores |
| LGPD | Média | Alto | Criptografia + termos |
| Adoção pelos dentistas | Média | Alto | UX simples + voz |
| Custo da API | Baixa | Médio | Modelos free + self-hosted |

---

## 9. Apêndice

### 9.1 Análise Competitiva Detalhada

Ver documento: `COMPETITIVE-ANALYSIS.md`

### 9.2 Base de Conhecimento (Livros RAG)

1. Tratamento Clínico Integrado em Odontologia — Feller & Lemos
2. Odontologia — História e Contexto
3. Diagnóstico Bucal
4. Emergências em Odontologia
5. Fundamentos de Prótese Fixa
6. Fundamentos de Oclusão
7. Genética Odontológica
8. Guia de Procedimentos em Odontologia
9. Manual de Cirurgia Oral
10. Manual de Dentística
11. Manual de Endodontia
12. Manual de Implantodontia
13. Manual de Ortodontia
14. Manual de Periodontia
15. Odontologia Legal
16. Odontopediatria
17. Patologia Oral
18. Planejamento em Odontologia
19. Radiologia Odontológica

### 9.3 Glossário

- **RAG:** Retrieval-Augmented Generation — técnica de IA que busca informações em uma base de conhecimento antes de gerar resposta
- **STT:** Speech-to-Text — transcrição de voz para texto
- **TTS:** Text-to-Speech — síntese de voz a partir de texto
- **PWA:** Progressive Web Application — app web que funciona como app nativo
- **VAD:** Voice Activity Detection — detecção de atividade vocal
- **LLM:** Large Language Model — modelo de linguagem grande (IA conversacional)
- **CRM:** Customer Relationship Management — gestão de relacionamento com pacientes

---

**Última atualização:** 12/06/2026
