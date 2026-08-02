# 2026-07-28: Formato correto do MCP no OpenCode 1.18.7

**Categoria:** config
**Contexto:** Ao adicionar servidor MCP no `opencode.jsonc`, o OpenCode 1.18.7 rejeitava a config com erro `Expected { readonly "type": "local", ... } | { readonly "type": "remote", ... }` e `Missing key mcp.servers.enabled`.
**Projetos afetados:** Todo o ecossistema (opencode.jsonc global)

## O erro

O formato **antigo** usado era:
```json
"mcp": {
  "servers": {
    "eco-knowledge": {
      "command": "python",
      "args": ["script.py"]
    }
  }
}
```

## O formato correto

No OpenCode 1.18.7, o schema `McpLocalConfig` exige:
1. `mcp` Ã© um objeto onde **cada chave Ã© o nome do servidor** (sem `servers` como wrapper)
2. `command` Ã© um **array Ãºnico** de strings (nÃ£o `command` + `args` separados)
3. `type` Ã© obrigatÃ³rio (`"local"` ou `"remote"`)

```json
"mcp": {
  "eco-knowledge": {
    "type": "local",
    "command": ["python", "C:/caminho/script.py"],
    "enabled": true
  }
}
```

## Fluxo de deploy seguro

Sempre testar antes de aplicar config:
1. `opencode debug config --pure` â€” valida schema bÃ¡sico
2. `opencode serve --pure` â€” carrega MCP, detecta erros de execuÃ§Ã£o
3. Manter `opencode.base.jsonc` limpo â€” sempre funciona
4. Usar `deploy-config.ps1` â€” testa e faz rollback automÃ¡tico em caso de falha

## ReferÃªncias
- Schema oficial: `https://opencode.ai/config.json` â†’ `$defs/McpLocalConfig`
- Script de deploy: `EcoSystemUmGrau/scripts/deploy-config.ps1`

## Conexoes

- [[cluster-hub-ecossistema]]