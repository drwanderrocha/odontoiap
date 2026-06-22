# Clinicorp - Análise Completa das Telas
## Mapeamento de Módulos e Funcionalidades

Wander, aqui está a análise completa das 61 screenshots da pasta "Clinicorp telas":

---

## 1. AGENDAS (Telas 1-2)
**Arquivos:** 105430, 105503

### Descrição:
- **Visão semanal** com grade horária (8:00 às 21:00, intervalos de 20min)
- **Calendário lateral** com mês de JUNHO, dia 21 destacado em vermelho
- **Filtro por dentista** no painel lateral
- **Alertas de retorno** na sidebar com lista de pacientes e datas
  - Ex: RITA DE CASSIA (1 mês), Valdemir Santos (08/06), etc.
  - Ícones de check verde para status concluído/confirmado
- **Busca global** no topo: "Encontre pacientes ou funções do sistema"
- **Perfil do usuário** no canto superior direito

### Elementos de UI:
- Colunas de dias da semana (Dom-Sáb)
- Eixo vertical de horas
- Cores diferentes para fins de semana
- Agenda vazia (sem agendamentos no momento do print)

---

## 2. PACIENTES - Listagem (Telas 3-6)
**Arquivos:** 105538, 105611, 105637, 105648

### Descrição:
- **Listagem de pacientes** em tabela
- **Busca por paciente** com campo de texto
- **Filtros** por status (ativo/inativo)
- **Botão "Novo Paciente"** para cadastro
- Colunas: Nome, CPF, Telefone, Email, Status, Ações

### Funcionalidades visíveis:
- Busca/filtro
- Paginação
- Ações por paciente (editar, visualizar, excluir)

---

## 3. PACIENTES - Cadastro/Perfil (Telas 7-10)
**Arquivos:** 105714, 105819, 105856, 105927

### Descrição:
- **Formulário de cadastro completo** com múltiplas abas/seções
- **Dados pessoais:** nome, apelido, data nascimento, sexo, CPF, RG, estado civil
- **Contato:** email, celular, telefone fixo, endereço completo
- **Dados complementares:** profissão, escolaridade, tipo sanguíneo, alergias, medicamentos
- **Upload de foto** do paciente
- **Status:** ativo/inativo

---

## 4. PRONTUÁRIO (Telas 11-13)
**Arquivos:** 105954, 110100, 110134

### Descrição:
- **Prontuário eletrônico** com múltiplas abas
- **Anamnese:** questionário de saúde com alertas
- **Odontograma:** representações dos dentes
- **Evolução:** acompanhamento de procedimentos
- **Documentos:** fotos, radiografias, exames
- **Histórico** de consultas

### Elementos:
- Abas de navegação horizontal
- Timeline de atendimentos
- Registro de procedimentos por dente
- Prescrições medicas
- Agendamento de retorno

---

## 5. FINANCEIRO - Dashboard Geral (Telas 14-17)
**Arquivos:** 110228, 110242, 110256, 110309

### Descrição:
- **Dashboard de indicadores (KPIs)** financeiros
- **Cards com métricas:** receita, despesa, saldo, inadimplência
- **Gráficos:** evolução mensal, categorias, formas de pagamento
- **Período selecionável** (mês/ano)

### Indicadores visíveis:
- Total de receitas
- Total de despesas
- Saldo do período
- Contas a pagar/receber
- Inadimplência

---

## 6. FINANCEIRO - Conta Corrente (Telas 18-22)
**Arquivos:** 110321, 110349, 110405, 110455, 110536

### Descrição:
- **Lançamentos financeiros** (entrada/saída)
- **Modal "Adicionar Lançamento"** com campos:
  - Tipo (receita/despesa)
  - Data
  - Categoria
  - Descrição
  - Valor
  - Forma de pagamento
  - Conta
- **Filtros por período** (data início/fim)
- **Tabela de extrato** com histórico

---

## 7. FINANCEIRO - Fluxo de Caixa (Telas 23-26)
**Arquivos:** 110555, 110619, 110649, 110711

### Descrição:
- **Visão projetada** de entradas e saídas
- **Agrupamento por categoria**
- **Filtros:** período, categoria, forma de pagamento
- **Gráfico de fluxo** temporal
- **Saldo acumulado**

---

## 8. FINANCEIRO - Controle de Boletos (Telas 27-29)
**Arquivos:** 110758, 110813, 110851

### Descrição:
- **Listagem de boletos** com status
- **Filtros:** data, status (Em Aberto, Pago, Todos)
- **Tabela:** número, paciente, valor, vencimento, status
- **Ações:** gerar, enviar por email

---

## 9. FINANCEIRO - Controle de Cheques (Tela 30)
**Arquivo:** 110908

### Descrição:
- **Listagem de cheques** recebidos
- **Campos:** número, banco, emitente, valor, data emissão, data vencimento, status
- **Filtros por período e status**

---

## 10. FINANCEIRO - Controle de Cartões (Tela 31)
**Arquivo:** 110923

### Descrição:
- **Transações de cartão** (crédito/débito)
- **Filtros:** data, bandeira, tipo
- **Tabela:** data, paciente, valor, parcelas, bandeira, status

---

## 11. FINANCEIRO - Controle de Planos (Tela 32)
**Arquivo:** 110936

### Descrição:
- **Convênios/Planos de saúde**
- **Tabela:** plano, tabela de preços, tipo, status
- **Filtros:** gale (convênio), tabela de preços, tipo

---

## 12. FINANCEIRO - Contas a Pagar (Telas 33-34)
**Arquivos:** 111010, 111028

### Descrição:
- **Cadastro e listagem** de contas a pagar
- **Modal "Nova Conta a Pagar":** fornecedor, descrição, valor, vencimento, categoria, recorrência
- **Filtros:** data, status, categoria
- **Tabela:** fornecedor, descrição, valor, vencimento, status

---

## 13. FINANCEIRO - Contas a Receber (Tela 35)
**Arquivo:** 111049

### Descrição:
- **Listagem de contas a receber**
- **Filtros:** data, status
- **Checkbox** para filtrar lançamentos sem check-out
- **Tabela:** paciente, descrição, valor, vencimento, status

---

## 14. FINANCEIRO - Metas (Telas 36-38)
**Arquivos:** 111059, 111127, 111147

### Descrição:
- **Configuração de metas** financeiras
- **Modal "Adicionar Meta":** tipo, descrição, valor, período
- **Dashboard de acompanhamento** vs realizado
- **Indicadores:** meta mensal, atingido, percentual

---

## 15. ESTOQUE - Materiais (Telas 39-40)
**Arquivos:** 111201, 111215

### Descrição:
- **Gestão de estoque/materiais**
- **Modal "Adicionar Material":** nome, categoria, quantidade mínima, unidade, valor unitário
- **Tabela de materiais** com estoque atual
- **Alertas de estoque baixo**

---

## 16. CONTROLE PROTÉTICO (Telas 41-43)
**Arquivos:** 111233, 111247, 111258

### Descrição:
- **Workflow Kanban** para próteses dentárias
- **Colunas de status:** Solicitado, Em Laboratório, Pronto, Instalado, etc.
- **Cards** com informações do paciente, tipo de prótese, datas
- **Modal "Pré-Envio"** para registro de envio ao laboratório
- **Campos:** paciente, tipo de trabalho, material, cor, data prevista, laboratório, observações

---

## 17. CURSOS/TREINAMENTOS (Telas 44-52)
**Arquivos:** 111310, 111322, 111334, 111358, 111420, 111432, 111512, 111533, 111551

### Descrição:
- **Gestão acadêmica** completa
- **Módulos do curso:** Dados Básicos, Módulos, Turmas, Alunos, Professores, Documentos
- **Cadastro de turmas:** nome, professor, vagas, valor, início, fim
- **Cadastro de alunos:** dados pessoais, matrícula, turma
- **Cadastro de professores:** nome, especialidade, CRO, contato
- **Documentos:** upload de materiais didáticos
- **Pacientes Modelos:** templates para simulação de orçamentos/treinamento
- **Materiais do curso:** lista de materiais necessários

---

## 18. GESTÃO DE ALINHADORES (Telas 53-55)
**Arquivos:** 111619, 111645, 111658

### Descrição:
- **Fluxo de trabalho** para alinhadores ortodônticos
- **Status:** Início, Pendente, Em Tratamento, Finalizado
- **Filtros:** paciente, status, período
- **Tabela:** paciente, início, etapa atual, próxima consulta

---

## 19. INTERESSADOS/LEADS (Telas 56-57)
**Arquivos:** 111711, 111723

### Descrição:
- **Funil de vendas** para cursos/procedimentos
- **Cards de indicadores:** total interessados, convertidos, perdidos
- **Filtros:** data, curso, turma
- **Tabela:** nome, contato, curso interessado, origem, status

---

## 20. CONFIGURAÇÕES - Mensagens (Telas 58-61)
**Arquivos:** 111819, 111832, 111850, 111914

### Descrição:
- **Templates de mensagens automáticas**
- **Canais:** E-mail, SMS, WhatsApp
- **Tipos:** Confirmação de consulta, Alerta de retorno, Aniversário, etc.
- **Editor de template** com variáveis dinâmicas
- **Configuração de horário** de envio

---

## RESUMO: MÓDULOS DO CLINICORP

| # | Módulo | Telas | Status |
|---|--------|-------|--------|
| 1 | **Agenda** | 1-2 | ✅ Mapeado |
| 2 | **Pacientes** (listagem + cadastro) | 3-10 | ✅ Mapeado |
| 3 | **Prontuário** (anamnese, odontograma, evolução) | 11-13 | ✅ Mapeado |
| 4 | **Financeiro** (dashboard, conta corrente, fluxo, boletos, cheques, cartões, planos, contas a pagar/receber, metas) | 14-38 | ✅ Mapeado |
| 5 | **Estoque** (materiais) | 39-40 | ✅ Mapeado |
| 6 | **Controle Protético** (workflow Kanban) | 41-43 | ✅ Mapeado |
| 7 | **Cursos/Treinamentos** (turmas, alunos, professores, documentos) | 44-52 | ✅ Mapeado |
| 8 | **Gestão de Alinhadores** | 53-55 | ✅ Mapeado |
| 9 | **Interessados/Leads** (funil de vendas) | 56-57 | ✅ Mapeado |
| 10 | **Configurações** (mensagens automáticas) | 58-61 | ✅ Mapeado |

---

## DIFERENCIAL DO ODONTOAI vs CLINICORP

| Funcionalidade | Clinicorp | OdontoAI (proposta) |
|---------------|-----------|---------------------|
| Agenda | ✅ Completa | ✅ + Voz |
| Pacientes | ✅ Completo | ✅ + Voz |
| Prontuário | ✅ 12 abas | ✅ + Voz + IA |
| Financeiro | ✅ Completo | ✅ Essencial |
| Estoque | ✅ | ✅ |
| Protético | ✅ Kanban | ❌ (futuro) |
| Cursos | ✅ Completo | ❌ (fora do escopo) |
| Alinhadores | ✅ | ❌ (futuro) |
| Interessados | ✅ | ✅ CRM simples |
| **Voz-first** | ❌ | ✅ **DIFERENCIAL** |
| **IA Copiloto Clínico** | ❌ | ✅ **DIFERENCIAL** |
| **RAG Literatura** | ❌ | ✅ **DIFERENCIAL** |
| **Open Source** | ❌ | ✅ **DIFERENCIAL** |
| **Preço** | R$150-370/mês | Gratuito/Open |

---

## PRÓXIMOS PASSOS

1. **Priorizar módulos** para o MVP do OdontoAI
2. **Definir fluxo de voz** para cada módulo
3. **Criar wireframes** das telas adaptadas para voz
4. **Implementar** o backend com Supabase
5. **Testar** com dentistas reais

Quer que eu detalhe algum módulo específico ou comece a implementação de algum? 🦷
