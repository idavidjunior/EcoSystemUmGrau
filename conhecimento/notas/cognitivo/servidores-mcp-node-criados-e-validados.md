---
tags: [apesar, closed, cognitivo, direto, funcionar, general]
aliases: [Servidores MCP Node criados e validados]
date: 2026-08-04
---

# Servidores MCP Node criados e validados

**Dominio:** general

> **DESCONTINUADO em 2026-09-05.** Os 4 servidores Node (filesystem, search,
> terminal, github) foram removidos do ecossistema: Node.js não está instalado no
> PC e todos duplicavam capacidades nativas do opencode ou MCPs Python já ativos.
> Este registro é histórico da criação; NÃO representa o estado atual do config.
> Ver [[2026-09-05-remocao-mcps-node-inoperantes]].

## O problema

1. `config/opencode.jsonc` apontava para `mcp-servers/mcp-servers/{filesystem,search,terminal,github}/index.js` (duplicação `mcp-servers/mcp-servers`), arquivos inexistentes.
2. `{{USERPROFILE}}` **não é resolvido** dentro do array `command` do MCP (só funciona em `instructions`). Por isso até o `eco-knowledge` (Python) falhava com "Connection closed" via opencode, apesar de funcionar direto no terminal.

## A correção

- `mcp-servers/lib/mcp-core.js` — classe `McpServer` (initialize â†’ tools/list â†’ tools/call, JSON-RPC 2.0, zero deps).
- `mcp-servers/filesystem/index.js` — list-dir, read-file, write
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]