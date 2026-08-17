---
tags: [330, atual, bridge, cognitivo, general, jarvis]
aliases: [MCP Obsidian server â€” vault consumido pelo LLM]
date: 2026-08-17
---

# MCP Obsidian server â€” vault consumido pelo LLM

**Dominio:** general

---
tipo: decisao
tags: [obsidian, mcp, infraestrutura, config, clausula-petrea, vault]
data: 2026-08-02
contexto: O vault Obsidian (docs/, conhecimento/, documentos/) estava sendo alimentado (330 notas .md) mas o LLM sÃ³ via a CONTAGEM de notas no estado da bridge (gerar_estado_atual em jarvis_bridge.py), nunca o conteÃºdo. Busca semÃ¢ntica via eco-knowledge cobria CONHECIMENTO.md e memory graph, mas nÃ£o os 327 .md de conhecimento/. Sem MCP server dedicado, sem file watcher.
decisao: Criar sc

﻿---
tipo: decisao
tags: [obsidian, mcp, infraestrutura, config, clausula-petrea, vault]
data: 2026-08-02
contexto: O vault Obsidian (docs/, conhecimento/, documentos/) estava sendo alimentado (330 notas .md) mas o LLM sÃ³ via a CONTAGEM de notas no estado da bridge (gerar_estado_atual em jarvis_bridge.py), nunca o conteÃºdo. Busca semÃ¢ntica via eco-knowledge cobria CONHECIMENTO.md e memory graph, mas nÃ£o os 327 .md de conhecimento/. Sem MCP server dedicado, sem file watcher.
decisao: Criar sc
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]