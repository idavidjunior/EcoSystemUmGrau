---
tags: [bug, providermcpserverpy]
aliases: [MCP server nao respondia a tools/call]
date: 2026-08-01
---

# MCP server nao respondia a tools/call

**Projeto:** provider_mcp_server.py

## Causa Raiz
Method tools/call nao estava no dispatch de handle_request()

## Correcao
Adicionado elif method == tools/call e _handle_tools_call() com mapping de nomes
## Conexoes

- [[bug-hub-bugs]]
- [[cluster-hub-ecossistema]]