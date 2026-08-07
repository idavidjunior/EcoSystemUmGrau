---
tags: [cognitivo, failed, general, github, ind, nome]
aliases: [Servidores MCP Node criados e validados]
date: 2026-08-06
---

# Servidores MCP Node criados e validados

**Dominio:** general

﻿---
tipo: padrao
tags: [mcp, infraestrutura, config, clausula-petrea]
data: 2026-08-02
contexto: DivergÃªncia detectada â€” config/opencode.jsonc referenciava 4 servidores MCP Node em `mcp-servers/mcp-servers/...` que nÃ£o existiam, e `{{USERPROFILE}}` nÃ£o Ã© resolvido em comandos MCP (apenas em instructions). `opencode mcp list` mostrava eco-knowledge/filesystem/search/terminal como "failed".
decisao: Criar os 4 servidores Node (filesystem, search, terminal, github) em `mcp-servers/<nome>/ind
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]