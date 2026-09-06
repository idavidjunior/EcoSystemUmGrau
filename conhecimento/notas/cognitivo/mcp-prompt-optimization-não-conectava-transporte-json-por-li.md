---
tags: [cognitivo, framing, general, length, padrão, rpc]
aliases: [MCP prompt-optimization não conectava: transporte JSON por l]
date: 2026-08-08
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

## Sintoma
O otimizador de prompt estava configurado (`config/opencode.jsonc` + deployed), o
`server.py` existia com 6 tools, mas **não ficava ativo**: nenhum processo rodava e
nenhuma tool era exposta nas sessões do opencode.

## Causa raiz
O `if __name__ == "__main__"` do `mcp/desenvolvimento/habilidades/prompt-optimization/server.py`
lia o stdin **linha a linha como JSON cru** (`for line in sys.stdin: json.loads(line)`).
O protocolo MCP sobre stdio (usado pelo opencode e por todos os clientes
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]