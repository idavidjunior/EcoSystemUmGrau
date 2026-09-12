---
tags: [agente, comando, compreensao, mcp]
aliases: [Compreender]
date: 2026-09-12
---

# compreender — Agente de Compreensão de Pedidos

**Categoria:** agentes
**Fonte:** config/agents/compreender.md

## Papel

Analisa o pedido do usuário antes de executar (objetivo, ações, conceitos, restrições, ambiguidades, desperdício) usando o MCP `mcp-compreensao-pedidos`.

## Gatilho

`@compreender <pedido>` ou `/compreender <pedido>`

## Responsabilidades

- Invocar `mcp-compreensao-pedidos:compreender_pedido`
- Validar score de clareza (≥60 para executar)
- Esclarecer ambiguidades se score < 60
- Detectar desperdício (repetição, scope creep)

## Conexões

- [[cluster-hub-ecossistema]] — hub do cluster ecossistema
- [[mcp-compreensao-pedidos]] — MCP de compreensão
- [[clausula-compreensao-pedidos]] — cláusula pétrea
- [[anti-bajulacao]] — comunicação direta
- [[10-aprendizado]] — registra aprendizado de compreensão