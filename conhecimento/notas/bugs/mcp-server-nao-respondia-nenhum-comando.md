---
tags: [bug, comando, obrigatorio, projeto, protocolo, sessaoprovidermanager]
aliases: [MCP server nao respondia nenhum comando]
date: 2026-08-08
---

# MCP server nao respondia nenhum comando

**Projeto:** sessao_providermanager

## Causa Raiz
Faltava handler para metodo initialize, que e obrigatorio no protocolo MCP

## Correcao
Adicionado _handle_initialize() com resposta de protocolVersion/capabilities
## Conexoes

- [[bug-hub-bugs]]
- [[cadeia-de-provedores-com-failover-inteligente]]
- [[cluster-hub-ecossistema]]
- [[mcp-server-handshake-obrigatorio]]
- [[opencode-go-provider-crash-ao-processar-mensagem]]
- [[server-failover-com-auto-return]]