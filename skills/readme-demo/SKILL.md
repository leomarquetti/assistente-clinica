---
name: readme-demo
description: Diretrizes para redação de README honesto, didático e completo para projetos de demonstração.
---

# Skill: Diretrizes de Documentação e README para Demonstrações

## Objetivo
Estruturar o arquivo `README.md` de projetos de portfólio de forma transparente, honesta e tecnicamente impecável, deixando evidentes o modo de demonstração, os limites da IA simulada, como reproduzir o projeto e os passos de evolução.

## Regras Obrigatórias
1. **Aviso Explícito de Modo Demo**: Deve constar no início do README o aviso claro de dados fictícios e IA simulada (baseada em regras).
2. **Frase-chave Visível**: Conter a frase exata: *"IA simulada; provider real plugável"*.
3. **Instruções Claras de Execução**: Passo a passo com `uv`/`pip`, variáveis de ambiente necessárias e comandos de teste.
4. **Decisões de Arquitetura Explicadas**: Diagrama de fluxo (Mermaid) demonstrando porque a privacidade e a triagem determinística ocorrem antes de qualquer IA.
5. **Limites Conhecidos**: Explicar expressamente o que o sistema NÃO faz (nunca dar conselho clínico ou diagnosticar).

## Exemplo Ruim ❌
```markdown
# Super Assistente IA com GPT-4 Médico
Este sistema atende pacientes automaticamente e faz diagnósticos com Inteligência Artificial avançada em produção!
```

## Exemplo Bom ✅
```markdown
# Assistente de Atendimento para Clínicas (Modo Demo)

> **AVISO**: Projeto de demonstração de portfólio. Aplica **boas práticas de privacidade inspiradas na LGPD** (mascaramento *best-effort*) e opera com **IA simulada; provider real plugável**.
> Não realiza diagnósticos médicos e não envia mensagens a pacientes sem aprovação humana.
```
