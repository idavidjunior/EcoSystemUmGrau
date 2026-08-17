---
tags: [bug, projeto, protocolo, providermcpserverpy52-55, quebrando, requests]
aliases: [MCP server Failed to get tools no OpenCode]
date: 2026-08-17
---

# MCP server Failed to get tools no OpenCode

**Projeto:** provider_mcp_server.py:52-55

## Causa Raiz
Server respondia a notifications JSON-RPC (requests sem id), quebrando protocolo

## Correcao
handle_request() retorna None se req_id is None; run() so escreve resposta se not None
## Conexoes

- [[bug-hub-bugs]]
- [[cluster-hub-ecossistema]]