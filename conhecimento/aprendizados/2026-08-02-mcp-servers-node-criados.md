---
tipo: padrao
tags: [mcp, infraestrutura, config, clausula-petrea]
data: 2026-08-02
contexto: DivergÃªncia detectada â€” config/opencode.jsonc referenciava 4 servidores MCP Node em `mcp-servers/mcp-servers/...` que nÃ£o existiam, e `{{USERPROFILE}}` nÃ£o Ã© resolvido em comandos MCP (apenas em instructions). `opencode mcp list` mostrava eco-knowledge/filesystem/search/terminal como "failed".
decisao: Criar os 4 servidores Node (filesystem, search, terminal, github) em `mcp-servers/<nome>/index.js` com core JSON-RPC stdio compartilhado (`mcp-servers/lib/mcp-core.js`), e usar paths absolutos no config MCP.
impacto: 5/5 MCP conectados; preflight_check.py passa em todos os testes; modelo usa tools via CLI (ex: `search_semantic-search`).
---

# Servidores MCP Node criados e validados

## O problema

1. `config/opencode.jsonc` apontava para `mcp-servers/mcp-servers/{filesystem,search,terminal,github}/index.js` (duplicaÃ§Ã£o `mcp-servers/mcp-servers`), arquivos inexistentes.
2. `{{USERPROFILE}}` **nÃ£o Ã© resolvido** dentro do array `command` do MCP (sÃ³ funciona em `instructions`). Por isso atÃ© o `eco-knowledge` (Python) falhava com "Connection closed" via opencode, apesar de funcionar direto no terminal.

## A correÃ§Ã£o

- `mcp-servers/lib/mcp-core.js` â€” classe `McpServer` (initialize â†’ tools/list â†’ tools/call, JSON-RPC 2.0, zero deps).
- `mcp-servers/filesystem/index.js` â€” list-dir, read-file, write-file, file-exists, search-in-files (restrito Ã  raiz do ecossistema, bloqueia escape de path).
- `mcp-servers/search/index.js` â€” semantic-search BM25 (knowledge_graph, CONHECIMENTO.md, memÃ³rias, Habilidades, aprendizados, notas) + search-overview.
- `mcp-servers/terminal/index.js` â€” run-command (PowerShell, timeout, bloqueia rm -rf/format/diskpart/shutdown/registry deletes) + shell-status.
- `mcp-servers/github/index.js` â€” gh-auth-status, gh-repo-list, gh-recent-commits, gh-repo-status (via `gh` CLI, token GH_TOKEN).
- Config: paths absolutos `C:/Users/David Jr/...` no `config/opencode.jsonc` e no deployed.

## ValidaÃ§Ã£o (regra: testar SEMPRE antes de aplicar)

1. Teste individual de cada servidor via stdin (initialize + tools/list + tools/call) â€” todos responderam corretamente.
2. `opencode debug config` â€” exit 0, sem erros.
3. `opencode mcp list` â€” 5/5 "connected" (antes: 4 failed + 1 disabled).
4. `opencode run` end-to-end â€” o modelo chamou `search_semantic-search` e retornou resultado real do KG.
5. `python scripts/preflight_check.py` â€” TODOS OS TESTES PASSARAM (inclui testar cada MCP com initialize + tools/list).

## LiÃ§Ã£o

- **`{{USERPROFILE}}` nÃ£o funciona em `command` de MCP no OpenCode** â€” usar paths absolutos (ou `{env:VAR}`).
- **Servidores MCP Node puros (stdlib)** sÃ£o permitidos (a clÃ¡usula proÃ­be `npx`, nÃ£o Node). `preflight_check.py` jÃ¡ testa cada um.
- Tool no modelo fica prefixada: `eco-knowledge_*`, `filesystem_*`, `search_*`, `terminal_*`, `github_*`.
- `opencode serve` com modelo free (ex: deepseek-v4-flash-free) pode nÃ£o expor tools ao modelo; via CLI (`opencode run`) com modelo da sessÃ£o (ex: z-ai/glm-5.2) as tools MCP funcionam.

## Conexoes

- [[2026-07-27-teste-do-vigilante-automático-teste-do-sistema-de]]
- [[cluster-hub-programacao]]