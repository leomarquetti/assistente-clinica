---
name: revisao-codigo-ia
description: Checklist e critérios para revisão crítica de código gerado por ferramentas de IA.
---

# Skill: Revisão Crítica de Código Gerado por IA

## Objetivo
Orientar desenvolvedores e agentes na auditoria rigorosa de código produzido por LLMs, prevenindo alucinações, dependências inventadas, falhas de validação e testes superficiais.

## Checklist de Revisão Obrigatório
1. **Dependências Inventadas**: Verificar se todas as bibliotecas importadas existem no `pyproject.toml` e possuem versões compatíveis.
2. **Validação de Entrada e Limites**: Garantir que campos textuais possuam limites de tamanho (`min_length`, `max_length`) para impedir DoS de memória.
3. **Prevenção de Vazamento de Segredos**: Auditar arquivos de configuração e exemplos (`.env.example`) para certificar que nenhum token real foi hardcoded.
4. **Tratamento de Exceções**: Conferir se blocos `try/except` capturam exceções específicas e se convertem em status HTTP sem expor stack traces sensíveis.
5. **Cobertura Real vs. Trivial**: Evitar testes que apenas testam mocks óbvios sem validar lógica real de negócio e transição de estados.

## Exemplo Ruim ❌
```python
# Ruim: Aceita payload arbitrário sem limites, expõe stack trace puro e usa lib inexistente
import fancy_ai_validator  # Pacote alucinado que não existe no PyPI


@router.post("/processar")
async def processar(dados: dict):  # Sem validação de tipos ou tamanho
    try:
        return fancy_ai_validator.validate(dados)
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}  # Vazamento de infraestrutura
```

## Exemplo Bom ✅
```python
# Bom: Modelo tipado Pydantic com limite, tratamento semântico e bibliotecas padrão
@router.post("/processar", response_model=RespostaProcessamento)
async def processar(payload: MensagemCriar):
    try:
        return await executar_servico(payload)
    except DominioException as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
```
