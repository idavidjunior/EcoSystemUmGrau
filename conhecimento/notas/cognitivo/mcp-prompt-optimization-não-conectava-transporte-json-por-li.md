---
tags: [cognitivo, framing, general, json, padrão, rpc]
aliases: [MCP prompt-optimization não conectava: transporte JSON por l]
date: 2026-08-20
---

# MCP prompt-optimization não conectava: transporte JSON por linha em vez de MCP stdio

**Dominio:** general

---
tipo: erro
tags: [mcp, prompt-optimization, transporte, stdio, content-length, opencode, jsonrpc]
data: 2026-08-08
contexto: Usuário perguntou se o otimizador de prompt estava ativo no ecossistema; verificação revelou que estava configurado mas nunca conectava
decisao: Corrigir o transporte do MCP server prompt-optimization para o padrão stdio com Content-Length framing (JSON-RPC MCP), em vez de JSON por linha
impacto: O MCP server agora responde a initialize/tools/list/tools/call com o prot
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]