---
tags: [bug, sessaoprovidermanager]
aliases: [MCP server nao respondia nenhum comando]
date: 2026-07-28
---

# Bug: MCP server nao respondia nenhum comando

**Projeto:** sessao_providermanager

## Causa Raiz
Faltava handler para metodo initialize, que e obrigatorio no protocolo MCP

## Correcao
Adicionado _handle_initialize() com resposta de protocolVersion/capabilities
