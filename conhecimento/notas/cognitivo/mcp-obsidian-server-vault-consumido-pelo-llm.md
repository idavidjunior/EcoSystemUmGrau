---
tags: [atual, check, cognitivo, general, jarvis, scripts]
aliases: [MCP Obsidian server — vault consumido pelo LLM]
date: 2026-08-20
---

# MCP Obsidian server — vault consumido pelo LLM

**Dominio:** general

---
tipo: decisao
tags: [obsidian, mcp, infraestrutura, config, clausula-petrea, vault]
data: 2026-08-02
contexto: O vault Obsidian (docs/, conhecimento/, documentos/) estava sendo alimentado (330 notas .md) mas o LLM só via a CONTAGEM de notas no estado da bridge (gerar_estado_atual em jarvis_bridge.py), nunca o conteúdo. Busca semântica via eco-knowledge cobria CONHECIMENTO.md e memory graph, mas não os 327 .md de conhecimento/. Sem MCP server dedicado, sem file watcher.
decisao: Criar sc

﻿---
tipo: decisao
tags: [obsidian, mcp, infraestrutura, config, clausula-petrea, vault]
data: 2026-08-02
contexto: O vault Obsidian (docs/, conhecimento/, documentos/) estava sendo alimentado (330 notas .md) mas o LLM só via a CONTAGEM de notas no estado da bridge (gerar_estado_atual em jarvis_bridge.py), nunca o conteúdo. Busca semântica via eco-knowledge cobria CONHECIMENTO.md e memory graph, mas não os 327 .md de conhecimento/. Sem MCP server dedicado, sem file watcher.
decisao: Criar sc

---
tipo: erro
tags: [preflight, mcp, playwright, timeout, resiliência, gate]
data: 2026-09-05
contexto: Durante o @sync, o gate persistencia.ps1 retornou PREFLIGHT_FAIL por 2x (22:37 e 22:43) com "MCP mcp-browser: Timeout (5s)", embora o preflight manual rodasse PASS (22:40) com o mesmo servidor.
decisao: A causa raiz era o timeout fixo de 5s no test_mcp_server (scripts/preflight_check.py, communicate(timeout=5)). O browser-mcp importa playwright.async_api no startup do processo que o teste spa
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]