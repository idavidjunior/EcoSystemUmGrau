---
tipo: erro
tags: [mcp, prompt-optimization, transporte, stdio, content-length, opencode, jsonrpc]
data: 2026-08-08
contexto: Usuário perguntou se o otimizador de prompt estava ativo no ecossistema; verificação revelou que estava configurado mas nunca conectava
decisao: Corrigir o transporte do MCP server prompt-optimization para o padrão stdio com Content-Length framing (JSON-RPC MCP), em vez de JSON por linha
impacto: O MCP server agora responde a initialize/tools/list/tools/call com o protocolo padrão; fica ativo na próxima sessão do opencode
---

# MCP prompt-optimization não conectava: transporte JSON por linha em vez de MCP stdio

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
- Probe com JSON cru por linha → respondia normalmente a `initialize` e `tools/list`.
Isso confirmou que a lógica do `handle()` estava correta; só o transporte estava errado.

## Correção aplicada
Substituído o loop de leitura por transporte MCP padrão:
- `_read_frame(stream)` — lê headers `Content-Length` do stdin.buffer e retorna o JSON.
- `_write_frame(stream, obj)` — escreve respostas com `Content-Length` framing.
- Loop principal: `_read_frame` → `handle(req)` → `_write_frame` (None = sem resposta,
  adequado para `notifications/initialized`).

## Verificação
Probe MCP padrão (framing correto) agora responde:
- `initialize` → `serverInfo: mcp-prompt-optimization v1.0.0`, capabilities tools.
- `tools/list` → 6 tools: optimize_prompt_dspy, refine_prompt_wizard, evaluate_prompt,
  compare_prompts, generate_prompt_tests, suggest_prompt_improvement.
- `tools/call evaluate_prompt` → scores (accuracy 100, overall 90, APP PROVED) OK.

## Lições
- Todo MCP server Python do ecossistema DEVE implementar o transporte stdio com
  **Content-Length framing** — "funcionar no terminal com echo" não significa que o
  opencode consiga usar.
- Ao criar/editar MCP servers, validar com um probe que faça `initialize` + `tools/list`
  + `tools/call` usando framing, não com pipe de JSON cru.
- A configuração no opencode.jsonc já apontava corretamente; o bug era 100% no server.

## Conexoes

- [[cluster-hub-programacao]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]