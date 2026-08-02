---
tipo: padrao
tags: [mcp, infraestrutura, config, clausula-petrea]
data: 2026-08-02
contexto: Divergência detectada — config/opencode.jsonc referenciava 4 servidores MCP Node em `mcp-servers/mcp-servers/...` que não existiam, e `{{USERPROFILE}}` não é resolvido em comandos MCP (apenas em instructions). `opencode mcp list` mostrava eco-knowledge/filesystem/search/terminal como "failed".
decisao: Criar os 4 servidores Node (filesystem, search, terminal, github) em `mcp-servers/<nome>/index.js` com core JSON-RPC stdio compartilhado (`mcp-servers/lib/mcp-core.js`), e usar paths absolutos no config MCP.
impacto: 5/5 MCP conectados; preflight_check.py passa em todos os testes; modelo usa tools via CLI (ex: `search_semantic-search`).
---

# Servidores MCP Node criados e validados

## O problema

1. `config/opencode.jsonc` apontava para `mcp-servers/mcp-servers/{filesystem,search,terminal,github}/index.js` (duplicação `mcp-servers/mcp-servers`), arquivos inexistentes.
2. `{{USERPROFILE}}` **não é resolvido** dentro do array `command` do MCP (só funciona em `instructions`). Por isso até o `eco-knowledge` (Python) falhava com "Connection closed" via opencode, apesar de funcionar direto no terminal.

## A correção

- `mcp-servers/lib/mcp-core.js` — classe `McpServer` (initialize → tools/list → tools/call, JSON-RPC 2.0, zero deps).
- `mcp-servers/filesystem/index.js` — list-dir, read-file, write-file, file-exists, search-in-files (restrito à raiz do ecossistema, bloqueia escape de path).
- `mcp-servers/search/index.js` — semantic-search BM25 (knowledge_graph, CONHECIMENTO.md, memórias, Habilidades, aprendizados, notas) + search-overview.
- `mcp-servers/terminal/index.js` — run-command (PowerShell, timeout, bloqueia rm -rf/format/diskpart/shutdown/registry deletes) + shell-status.
- `mcp-servers/github/index.js` — gh-auth-status, gh-repo-list, gh-recent-commits, gh-repo-status (via `gh` CLI, token GH_TOKEN).
- Config: paths absolutos `C:/Users/David Jr/...` no `config/opencode.jsonc` e no deployed.

## Validação (regra: testar SEMPRE antes de aplicar)

1. Teste individual de cada servidor via stdin (initialize + tools/list + tools/call) — todos responderam corretamente.
2. `opencode debug config` — exit 0, sem erros.
3. `opencode mcp list` — 5/5 "connected" (antes: 4 failed + 1 disabled).
4. `opencode run` end-to-end — o modelo chamou `search_semantic-search` e retornou resultado real do KG.
5. `python scripts/preflight_check.py` — TODOS OS TESTES PASSARAM (inclui testar cada MCP com initialize + tools/list).

## Lição

- **`{{USERPROFILE}}` não funciona em `command` de MCP no OpenCode** — usar paths absolutos (ou `{env:VAR}`).
- **Servidores MCP Node puros (stdlib)** são permitidos (a cláusula proíbe `npx`, não Node). `preflight_check.py` já testa cada um.
- Tool no modelo fica prefixada: `eco-knowledge_*`, `filesystem_*`, `search_*`, `terminal_*`, `github_*`.
- `opencode serve` com modelo free (ex: deepseek-v4-flash-free) pode não expor tools ao modelo; via CLI (`opencode run`) com modelo da sessão (ex: z-ai/glm-5.2) as tools MCP funcionam.
