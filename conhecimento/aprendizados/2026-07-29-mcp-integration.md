# 2026-07-29 â€” MCP Integration

## Learning
Integrated 5 MCP servers from `opencode-agents-mcp` repo into EcoSystemUmGrau:
- **eco-knowledge** (Python) â€” knowledge server for semantic search
- **filesystem** (Node.js) â€” file operations
- **search** (Node.js) â€” web search
- **terminal** (Node.js) â€” command execution
- **github** (Node.js, disabled) â€” GitHub API; needs GH_TOKEN env var

## Config Schema (opencode v1.18.9)
- `mcp` is a plain object: keys = server names, values = server configs (no `servers` wrapper)
- Each server requires: `"type": "local"` and `"command": ["executable", "arg1", ...]` (array, not string + args)
- Optional: `"enabled": bool`, `"environment": { "VAR": "{env:VAR}" }`
- `environment` (not `env`)
- Booleans `mcp: true` or `mcp.enabled` or `mcp.servers.enabled` all **fail** schema

## Status
- Config validated successfully (`opencode debug config` returns no errors)
- filesystem MCP server starts on stdio and accepts JSON-RPC
- GitHub disabled until GH_TOKEN set
- better-sqlite3 native addon does not compile on this machine (no VS Build Tools) â€” database server unavailable
- Memory critical (~440MB free of 4GB) â€” guardian may kill processes

## Repos
- `mcp-servers/` cloned from `AliZafar780/opencode-agents-mcp` (depth 1)
- npm deps installed with `--ignore-scripts`

## Conexoes

- [[cluster-hub-programacao]]