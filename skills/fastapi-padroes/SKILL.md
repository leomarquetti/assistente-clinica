---
name: fastapi-padroes
description: Padrões de arquitetura limpa, separação de camadas e boas práticas em FastAPI.
---

# Skill: Padrões de Arquitetura FastAPI

## Objetivo
Estruturar aplicações FastAPI em camadas desacopladas (`api`, `domain`, `services`, `providers`, `storage`), garantindo injeção de dependências eficiente, validação estrita com Pydantic v2 e tratamento semântico de erros HTTP.

## Regras Obrigatórias
1. **Separação de Camadas**: Rotas (`api/`) apenas recebem requisições e delegam para serviços (`services/`). Lógica de negócio nunca deve residir diretamente no corpo da rota.
2. **Schemas Pydantic v2**: Utilizar schemas explícitos para entrada e saída com validação de limites de tamanho (`max_length`, `min_length`).
3. **Injeção de Dependências**: Utilizar `Depends()` para prover serviços e storage, permitindo fácil substituição em testes.
4. **Erros Semânticos**: Mapear erros de domínio para códigos HTTP adequados:
   - Recurso não encontrado -> `404 Not Found`
   - Transição inválida de estado -> `409 Conflict`
   - Falha de autorização -> `401 Unauthorized` ou `403 Forbidden`
   - Payload inválido -> `422 Unprocessable Content` (sem vazar PII)

## Exemplo Ruim ❌
```python
# Ruim: Conexão direta com banco na rota, sem validação nem DTO de resposta
@router.post("/mensagens")
async def criar(texto: str):
    db = sqlite3.connect("banco.db")
    db.execute(f"INSERT INTO mensagens VALUES ('{texto}')")  # Risco SQL injection
    return {"status": "ok"}
```

## Exemplo Bom ✅
```python
# Bom: Schema Pydantic validado, injeção de dependência e tratamento de exceções de domínio
@router.post("/mensagens/{id}/aprovar", response_model=MensagemResponse)
async def aprovar(
    id: str,
    payload: AprovacaoRequest,
    pipeline: PipelineService = Depends(get_pipeline_service),
    role: RoleEnum = Depends(require_atendente),
):
    try:
        return await pipeline.aprovar_mensagem(id, payload, operador_autenticado=role.value)
    except StateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
```
