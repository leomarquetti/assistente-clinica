# Regras do Projeto para Agentes Autônomos de Código (AGENTS.md)

Este documento estabelece as restrições inegociáveis, convenções de desenvolvimento e arquitetura para qualquer assistente ou agente de IA (Antigravity, Claude Code, Cursor, etc.) que atue neste repositório.

---

## 1. Princípios Inegociáveis do Projeto

1. **Segurança Clínica & Human-in-the-Loop Estrito**:
   - O sistema **JAMAIS** responde a dúvidas clínicas, prescreve medicamentos ou sugere diagnósticos.
   - Nenhuma mensagem é despachada diretamente ao paciente sem revisão e aprovação humana explícita (`POST /mensagens/{id}/aprovar`).
   - A detecção de urgência clínica é **sempre determinística** e executada **antes** e **independentemente** de qualquer provedor de IA.
   - **Nenhum provedor (mock ou real) tem permissão de rebaixar uma urgência médica detectada.**

2. **Boas Práticas de Privacidade (Inspiradas na LGPD)**:
   - Todo dado recebido do paciente deve passar por sanitização e mascaramento *best-effort* antes de ser persistido, auditado ou repassado a provedores de LLM.
   - O mascaramento se aplica a: `texto`, `paciente_identificador`, `texto_aprovado` e `observacoes`.
   - O handler de `RequestValidationError` (HTTP 422) nunca deve ecoar o campo `input` do usuário com dados brutos não validados.
   - A trilha de auditoria deve ser estritamente *append-only*.

3. **Arquitetura Desacoplada ("IA simulada; provider real plugável")**:
   - A substituição do mock baseado em regras por um provedor real deve ocorrer exclusivamente via variável de ambiente (`LLM_PROVIDER=real` com `LLM_API_KEY` apenas no servidor), sem qualquer modificação no restante do código.
   - Só declare que integrou um LLM real quando isso for verdadeiro e estiver homologado.

---

## 2. Padrões de Código e Convenções

- **Stack**: Python 3.12+, FastAPI, Pydantic v2, Uvicorn, SlowAPI.
- **Camadas**:
  - `app/api/`: Definição de rotas, injeção de dependências e mapeamento de status HTTP.
  - `app/domain/`: Schemas Pydantic de entrada/saída, enums de intenções e máquina de estados finitos.
  - `app/services/`: Lógica de negócio determinística (privacidade, triagem, pipeline, rascunhos, auditoria).
  - `app/providers/`: Integração plugável com IA (mock baseado em regras determinísticas ou stub real).
  - `app/storage/`: Interfaces e drivers de armazenamento (`memory` para testes e `sqlite` para persistência local).
- **Tipagem**: `strict = true` no Mypy. Todos os parâmetros e retornos de funções devem ser tipados.
- **Estilo & Qualidade**: Formatação e linting padronizados pelo Ruff (`ruff check .` e `ruff format .`).

---

## 3. Checklist Obrigatório para Agentes de Código

Antes de dar uma tarefa por concluída, o agente deve:
- [ ] Garantir que `.env` continua no `.gitignore` e que `.env.example` não contém segredos reais.
- [ ] Executar a suite completa de testes com `pytest -v` e confirmar 100% de sucesso.
- [ ] Executar o linter e o formatador (`ruff check .`, `ruff format --check .`) sem erros.
- [ ] Executar a checagem estática de tipos (`mypy app tests`) sem erros.
- [ ] Verificar que nenhuma mensagem clínica automática foi criada sem supervisão humana.
- [ ] Verificar se transições inválidas de estados retornam HTTP 409 Conflict.
- [ ] Consultar e respeitar as skills disponíveis no diretório `skills/`.
