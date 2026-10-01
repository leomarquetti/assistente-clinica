---
name: seguranca-lgpd
description: Diretrizes de boas práticas de privacidade e segurança no desenvolvimento com dados médicos e pessoais.
---

# Skill: Segurança & Boas Práticas de Privacidade

## Objetivo
Garantir que nenhum dado pessoal identificável (PII) ou segredo de autenticação seja exposto, persistido em texto claro, logado ou enviado a provedores de inteligência artificial de forma insegura.

## Regras Obrigatórias
1. **Nunca comitar segredos**: Chaves de API, senhas e tokens devem ser lidos estritamente via variáveis de ambiente (.env).
2. **Mascaramento antes de qualquer IA**: O texto bruto deve passar por sanitização *best-effort* antes de ser repassado ao `LLMProvider` ou gravado em storage.
3. **Auditoria Append-Only Sanitizada**: Registros de auditoria devem conter apenas identificadores e textos já devidamente mascarados.
4. **Sem Eco em Erros de Validação**: Handlers de erro 422 nunca devem ecoar o campo `input` original do usuário na resposta.
5. **RLS e Isolamento**: Em bancos relacionais, aplicar Row-Level Security (RLS) e permissões de menor privilégio.

## Exemplo Ruim ❌
```python
# Ruim: loga o CPF em texto claro e envia o dado bruto diretamente para a IA
@router.post("/atendimento")
async def atendimento(mensagem: str, cpf: str):
    logger.info(f"Recebendo mensagem do paciente CPF {cpf}: {mensagem}")
    resposta_ia = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"O paciente {cpf} disse: {mensagem}"}],
    )
    return {"resposta": resposta_ia}
```

## Exemplo Bom ✅
```python
# Bom: mascara deterministicamente antes do log e do acionamento do LLM
@router.post("/atendimento")
async def atendimento(
    payload: MensagemCriar, pipeline: PipelineService = Depends(get_pipeline_service)
):
    # O pipeline mascara CPF, telefone, e-mail e nomes antes de registrar no log append-only
    resultado = await pipeline.processar_mensagem(payload)
    # resposta contém apenas texto_mascarado e rascunho administrativo para aprovação
    return resultado
```
