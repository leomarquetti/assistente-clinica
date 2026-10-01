# Product Requirements Document (PRD)
## Assistente de Atendimento para Clínicas (Modo Demo)

---

### 1. Visão do Produto & Declaração de Escopo
O **Assistente de Atendimento para Clínicas** é um projeto de demonstração e portfólio de engenharia de software voltado ao setor da saúde, demonstrando arquitetura modular, segurança preventiva e **boas práticas de privacidade inspiradas na LGPD**.

> [!WARNING]
> **Aviso Obrigatório de Demonstração e Limites Médicos**:
> - Esta aplicação opera estritamente em **modo de demonstração** com **IA simulada (baseada em regras)** e dados 100% fictícios.
> - **Frase-chave de Arquitetura**: *"IA simulada; provider real plugável."*
> - **O sistema NUNCA responde a dúvidas clínicas, NÃO sugere diagnósticos e NUNCA envia mensagens aos pacientes sem aprovação humana expressa.**
> - O mascaramento de dados pessoais é assumidamente **best-effort** (heurístico e baseado em expressões regulares com validação algorítmica).

---

### 2. O Que o Sistema Faz vs. O Que Não Faz

| O Sistema Faz | O Sistema Não Faz |
| :--- | :--- |
| Recebe mensagens de pacientes fictícios via API REST | Responder dúvidas clínicas ou terapêuticas |
| Aplica mascaramento *best-effort* de dados sensíveis antes de qualquer IA | Sugerir diagnósticos médicos ou dosagens de medicamentos |
| Triagem determinística de urgência com normalização e análise de negação | Rebaixar urgência médica detectada em qualquer hipótese |
| Classifica intenções administrativas (agendamento, remarcação, administrativo, financeiro) | Enviar mensagens automaticamente a pacientes sem aprovação humana |
| Sugere rascunho de resposta administrativa para aprovação da equipe | Persistir dados pessoais (CPF, celular, etc.) em texto claro |
| Registra histórico em trilha de auditoria *append-only* | Operar em modo de produção real com pacientes reais |
---

### 3. Personas & Casos de Uso

#### Persona 1: Atendente / Recepcionista da Clínica
- **Objetivo**: Triar rapidamente a demanda administrativa do paciente fictício, revisar o rascunho sugerido pelo assistente, realizar ajustes quando pertinente e aprovar o texto final para envio.
- **Fluxo Principal**:
  1. Acessa mensagens em status `aguardando_aprovacao`.
  2. Inspeciona o texto mascarado, a intenção detectada e o rascunho.
  3. Aciona o endpoint `POST /mensagens/{id}/aprovar` com sua credencial de atendente, registrando seu nome no log de auditoria append-only.

#### Persona 2: Gestor da Clínica / Encarregado de Privacidade (DPO)
- **Objetivo**: Auditar as operações, verificar o cumprimento das políticas de privacidade, garantir que nenhum dado pessoal vazou e que todas as transições de estado foram autenticadas.
- **Fluxo Principal**:
  1. Acessa o endpoint `GET /auditoria` com sua chave exclusiva de gestor.
  2. Analisa os registros *append-only* cronológicos e detalhados.

#### Persona 3: Paciente Fictício
- **Objetivo**: Solicitar agendamento, reagendamento, tirar dúvidas sobre convênios ou solicitar recibo/nota fiscal de atendimento.

---

### 4. Requisitos Funcionais (RF)

- **RF01 - Sanitização e Mascaramento Preventivo (Best-Effort)**:
  - Mascarar deterministicamente antes de qualquer persistência, log ou acionamento de IA:
    - **CPF**: validação dos dígitos verificadores (diferenciando de celulares de 11 dígitos com DDD).
    - **Telefone**: celulares (9 dígitos) e números fixos (8 dígitos), com ou sem DDD e código internacional.
    - **E-mails**: regex padrão RFC.
    - **CEP**: formatos `XXXXX-XXX` e sequências numéricas após identificador de CEP.
    - **RG**: padrões estaduais comuns e sequências após identificador de RG.
    - **Data de Nascimento**: formato `DD/MM/AAAA`.
    - **Nomes Próprios**: autoidentificações declaradas ("me chamo", "sou o", etc.) e nomes compostos capitalizados.
  - O mascaramento deve ser estendido a `paciente_identificador`, `texto_aprovado` e `observacoes`.

- **RF02 - Detecção Determinística de Urgência Clínica**:
  - Executada **antes e independentemente** de qualquer provedor de IA.
  - Normalização prévia de texto: remoção de acentos via decomposição Unicode (NFKD), conversão para minúsculas e limpeza de espaçamento.
  - Verificação de termos de urgência (dor no peito, falta de ar, sangramento, desmaio, convulsão, etc.).
  - Análise semântica de negação ("não estou com dor no peito", "sem falta de ar", "não sinto febre nem falta de ar").
  - Se urgência ativa for detectada:
    - `intencao = URGENCIA_CLINICA`
    - `confianca = 1.0`
    - `requer_atencao_humana = True`
    - **Bloqueio total de rascunho automatizado de resposta.**
    - **Regra de ouro**: Nenhum provedor pode rebaixar a urgência clínica.

- **RF03 - Classificação de Intenções Administrativas**:
  - Classificação léxica determinística entre:
    - `AGENDAMENTO`
    - `REMARCACAO`
    - `DUVIDA_ADMINISTRATIVA`
    - `FINANCEIRO`
    - `OUTRO`
  - Se a confiança for inferior ao limiar (`CONFIDENCE_THRESHOLD=0.6`), escalonar imediatamente para atenção humana sem rascunho de IA.

- **RF04 - Provedor de LLM Plugável**:
  - Interface abstrata `LLMProvider`.
  - `MockLLMProvider`: simulador baseado em regras determinísticas para testes e demonstração.
  - `RealLLMProvider`: stub seguro que exige configuração explícita de chave no servidor para ativação futura.

- **RF05 - Máquina de Estados e Human-in-the-Loop**:
  - Estados: `recebida`, `aguardando_aprovacao`, `requer_atencao_humana`, `aprovada`, `rejeitada`.
  - Estados terminais (sem novas transições permitidas): `aprovada` e `rejeitada`.
  - Tentativas de transição inválida devem retornar **HTTP 409 Conflict**.

- **RF06 - Trilha de Auditoria Append-Only**:
  - Registros append-only com id único, timestamp UTC, mensagem_id, ação, operador autenticado e detalhes mascarados.
  - Proteção estrita de acesso: liberado exclusivamente para o papel `gestor`.

- **RF07 - Autenticação por API Key e Rate Limiting**:
  - Cabeçalho `X-API-Key` validando papéis `atendente` e `gestor`.
  - Rate limiting via `slowapi` limitando requisições abusivas.

---

### 5. Requisitos Não-Funcionais (RNF)

- **RNF01 - Segurança e Não-Vazamento de PII**:
  - Handler customizado para `RequestValidationError` (HTTP 422) garantindo que payloads rejeitados não ecoem o campo `input` com dados sensíveis.
  - Garantia formal (coberta por testes automatizados) de que nenhum dado pessoal bruto permaneça em disco, logs ou respostas.
- **RNF02 - Persistência Flexível**:
  - Suporte out-of-the-box para `memory` (testes efêmeros) e `sqlite` (persistência local relacional em arquivo).
- **RNF03 - Qualidade e Tipagem Estrita**:
  - Tipagem estrita com `mypy` sem supressões não justificadas.
  - Linting e formatação com `Ruff`.
  - Testes com `pytest` cobrindo 100% dos caminhos críticos.
- **RNF04 - Containerização Segura**:
  - Dockerfile com versão fixada do Python (`3.12.9-slim-bookworm`), execução obrigatória via usuário não-root (`appuser`, UID 10001) e healthcheck integrado.

---

### 6. Matriz de Transição da Máquina de Estados

| Estado Atual | Destino Permitido | Ação / Gatilho | HTTP Status |
| :--- | :--- | :--- | :--- |
| `RECEBIDA` | `AGUARDANDO_APROVACAO` | Triagem com confiança ≥ limiar e sem urgência | 201 Created |
| `RECEBIDA` | `REQUER_ATENCAO_HUMANA` | Urgência detectada ou confiança < limiar | 201 Created |
| `AGUARDANDO_APROVACAO` | `APROVADA` | Atendente/Gestor aprova via `POST /aprovar` | 200 OK |
| `AGUARDANDO_APROVACAO` | `REJEITADA` | Atendente/Gestor descarta via `POST /rejeitar` | 200 OK |
| `REQUER_ATENCAO_HUMANA` | `APROVADA` | Operador insere texto manual via `POST /aprovar` | 200 OK |
| `REQUER_ATENCAO_HUMANA` | `REJEITADA` | Operador encerra via `POST /rejeitar` | 200 OK |
| `APROVADA` | *Qualquer destino* | Reaprovação ou alteração de estado terminal | **409 Conflict** |
| `REJEITADA` | *Qualquer destino* | Reativação de mensagem rejeitada | **409 Conflict** |

---

### 7. Roadmap de Evolução

- **Fase 1 (Concluída - Demo Atual)**:
  - Triagem determinística, mascaramento *best-effort*, máquina de estados, autenticação simples por papel, log *append-only*, testes automatizados.
- **Fase 2 (Concluída - Persistência e Infraestrutura)**:
  - SQLite persistente, Docker seguro com usuário não-root, Docker Compose e GitHub Actions CI com Gitleaks.
- **Fase 3 (Futura - Base de Conhecimento e LLM Real)**:
  - Busca semântica vetorial em base de procedimentos da clínica (PostgreSQL + pgvector).
  - Ativação do `RealLLMProvider` com teto de gasto mensal e chaves injetadas via Vault/Secret Manager.
