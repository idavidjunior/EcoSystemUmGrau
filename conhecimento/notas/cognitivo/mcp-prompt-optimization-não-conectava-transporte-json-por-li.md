---
tags: [buffer, clientes, cognitivo, general, payload, usa]
aliases: [MCP prompt-optimization não conectava: transporte JSON por l]
date: 2026-08-08
---

# MCP prompt-optimization não conectava: transporte JSON por linha em vez de MCP stdio

**Dominio:** general

## Sintoma
O otimizador de prompt estava configurado (`config/opencode.jsonc` + deployed), o
`server.py` existia com 6 tools, mas **não ficava ativo**: nenhum processo rodava e
nenhuma tool era exposta nas sessões do opencode.

## Causa raiz
O `if __name__ == "__main__"` do `mcp/desenvolvimento/habilidades/prompt-optimization/server.py`
lia o stdin **linha a linha como JSON cru** (`for line in sys.stdin: json.loads(line)`).
O protocolo MCP sobre stdio (usado pelo opencode e por todos os clientes MCP) usa
**framing Content-Length** (estilo LSP):

```
Content-Length: 123\r\n
\r\n
{jsonrpc...}
```

Ao conectar, o opencode enviava frames; o server recebia a linha `Content-Length: N`
(JSON inválido → descartada) e a linha vazia (ignorada) e o payload ficava no buffer
sem nunca ser lido. Resultado: handshake `initialize` nunca completava → server nunca
aparecia como online.

## Prova
- Probe com framing padrão → **nenhuma resposta** (timeout de 60s).
- Probe com JSON cru por linha → respondi
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]