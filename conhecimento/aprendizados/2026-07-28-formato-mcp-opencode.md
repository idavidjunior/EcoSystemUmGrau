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
1. `mcp` é um objeto onde **cada chave é o nome do servidor** (sem `servers` como wrapper)
2. `command` é um **array único** de strings (não `command` + `args` separados)
3. `type` é obrigatório (`"local"` ou `"remote"`)

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
1. `opencode debug config --pure` — valida schema básico
2. `opencode serve --pure` — carrega MCP, detecta erros de execução
3. Manter `opencode.base.jsonc` limpo — sempre funciona
4. Usar `deploy-config.ps1` — testa e faz rollback automático em caso de falha

## Referências
- Schema oficial: `https://opencode.ai/config.json` → `$defs/McpLocalConfig`
- Script de deploy: `EcoSystemUmGrau/scripts/deploy-config.ps1`
