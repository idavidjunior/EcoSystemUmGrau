---
tags: [busc, busqu, estruturada, fonte, opencode, padrao]
aliases: [Módulo de Compreensão de Pedidos (mcp-compreensao-pedidos)]
date: 2026-08-08
---

# Módulo de Compreensão de Pedidos (mcp-compreensao-pedidos)

**Fonte:** opencode

Substitui o pipeline DSPy/PromptWizard de otimização de prompts. Em vez de polir o
prompt, o ecossistema agora COMPREENDE o pedido e o converte em ação estruturada.

## Estrutura

```
mcp/nucleo/habilidades/compreensao-pedidos/
  compreensao.py   # núcleo stdlib, CLI, importável (CPython puro)
  server.py        # MCP server (5 tools), transporte stdio dual
  skill.md         # instruções de uso
```

## O que faz (estático, instantâneo, sem LLM)

- **Ações explícitas** extraídas por radicais de verbo (com variantes c→qu da
  conjugação: `explic|expliqu`, `verific|verifiqu`, `chec|chequ`, `busc|busqu`)
  e **ordenadas por posição de aparição no texto** (não por ordem da regex).
- **Objeto da ação** cortado no próximo verbo e em "e <verbo>" (com split por
  stopwords: "e me diga", "e faça o backup").
- **Verbos auxiliares genéricos** ("faça", "faz") descartados quando imediatamente
  antes de outra ação real.
- **Conceitos** = entidades conhecidas (projetos/skills/scripts) + termos
  cap
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]