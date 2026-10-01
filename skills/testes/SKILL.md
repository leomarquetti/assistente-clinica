---
name: testes
description: Boas práticas para construção de suites de testes automatizados com pytest e httpx.
---

# Skill: Boas Práticas de Testes Automatizados

## Objetivo
Assegurar que toda funcionalidade crítica, regra de segurança e caso de borda seja coberto por testes determinísticos, isolados e rápidos, utilizando pytest e TestClient.

## Regras Obrigatórias
1. **Pytest Primeiro nas Partes Críticas**: Priorizar testes de mascaramento LGPD, validação matemática de documentos e detecção de urgência clínica.
2. **Mocks Determinísticos**: Provedores de IA simulados devem ser 100% reproduzíveis, sem chamadas de rede externas e sem aleatoriedade nos testes.
3. **Casos de Borda Obrigatórios**:
   - Negações semânticas ("não sinto dor", "sem falta de ar").
   - CPFs matematicamente válidos vs. números de telefone celular com DDD.
   - Transições inválidas da máquina de estados (conflito 409).
4. **Isolamento de Estado**: Cada teste deve iniciar com armazenamento limpo (via fixtures com autouse).

## Exemplo Ruim ❌
```python
# Ruim: Teste que depende de API externa com custo e latência imprevisível
def test_ia_resposta():
    client = OpenAI()
    resposta = client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": "Olá"}]
    )
    assert len(resposta.choices) > 0  # Não testa regras de negócio nem limites
```

## Exemplo Bom ✅
```python
# Bom: Teste determinístico de caso de borda de urgência clínica com negação
def test_detectar_urgencia_com_negacao():
    texto = "Não estou com dor no peito, apenas quero agendar um exame."
    triagem = executar_triagem_deterministica(texto)
    assert triagem.intencao != IntentEnum.URGENCIA_CLINICA
    assert triagem.requer_atencao_humana is False
```
