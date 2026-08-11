---
tipo: decisao
tags: [obsidian, mcp, infraestrutura, config, clausula-petrea, vault]
data: 2026-08-02
contexto: O vault Obsidian (docs/, conhecimento/, documentos/) estava sendo alimentado (330 notas .md) mas o LLM sÃ³ via a CONTAGEM de notas no estado da bridge (gerar_estado_atual em jarvis_bridge.py), nunca o conteÃºdo. Busca semÃ¢ntica via eco-knowledge cobria CONHECIMENTO.md e memory graph, mas nÃ£o os 327 .md de conhecimento/. Sem MCP server dedicado, sem file watcher.
decisao: Criar scripts/mcp-obsidian-server.py (Python puro) com 4 tools MCP: list-vault (listar .md), read-note (ler nota), search-vault (busca BM25 no conteÃºdo), vault-summary (estatÃ­sticas). Adicionar ao config/opencode.jsonc e deployar.
impacto: LLM agora consome o conteÃºdo real do vault via MCP. Preflight 6/6 PASS (eco-obsidian incluÃ­do). Deploy aprovado (schema + serve iniciou). Antes: bridge contava notas (330). Depois: busca e leitura direta do conteÃºdo.
---

# MCP Obsidian server â€” vault consumido pelo LLM

## O problema

O "Obsidian" do ecossistema Ã© uma estrutura de pastas com markdown:

- `docs/` (3 notas: arquitetura, auditoria, ecossistema)
- `conhecimento/` (327 notas: aprendizados, decisÃµes, cognitivo)
- `documentos/` (0 notas)

A bridge (`jarvis_bridge.py`) sÃ³ expunha a **contagem** de arquivos ao LLM
("Total vault: 330 notas"). O LLM sabia que existiam, mas nunca lia o conteÃºdo.
A busca semÃ¢ntica (`eco-knowledge` / `search`) cobria `CONHECIMENTO.md`,
`memories.json` e o knowledge graph â€” mas **nÃ£o** os 327 arquivos `conhecimento/`.

## A soluÃ§Ã£o

Criado `scripts/mcp-obsidian-server.py` â€” Python puro, JSON-RPC 2.0 via stdio,
mesmo padrÃ£o do `mcp-knowledge-server.py`.

### Tools expostas

| Tool | DescriÃ§Ã£o |
|------|-----------|
| `list-vault` | Lista diretÃ³rios e arquivos .md do vault (recursivo opcional) |
| `read-note` | LÃª conteÃºdo de uma nota .md (com offset/limit) |
| `search-vault` | Busca BM25 simples no conteÃºdo de todas as notas |
| `vault-summary` | EstatÃ­sticas: total de notas por diretÃ³rio |

SeguranÃ§a: `safe_resolve()` bloqueia traversal de path fora do ecossistema.

## ValidaÃ§Ã£o (regra: testar SEMPRE antes de aplicar)

1. Teste individual via stdin (initialize + tools/list) â€” respondeu corretamente.
2. Teste de cada tool:
   - `vault-summary` â†’ `{"total_notes": 330, docs: 3, conhecimento: 327, documentos: 0}`
   - `search-vault "tts prosody"` â†’ 18 hits com excertos reais
   - `read-note docs/jarvis-arquitetura.md` â†’ conteÃºdo completo da nota
   - `list-vault conhecimento/aprendizados recursive` â†’ 59 notas listadas
3. `python scripts/preflight_check.py` â€” TODOS OS TESTES PASSARAM (6/6 MCP).
4. Deploy via `deploy-config.ps1` â€” schema vÃ¡lido + `opencode serve` iniciou com MCP carregado.
5. Backup criado antes do deploy (`opencode.jsonc.bak`).

## Estado final

- Template `config/opencode.jsonc`: 6 MCP servers (eco-knowledge, filesystem, search, terminal, github, **eco-obsidian**).
- Deployed `~/.config/opencode/opencode.jsonc`: idem, aprovado.
- A sessÃ£o atual do OpenCode precisa reiniciar para expor as tools `eco-obsidian_*` (as tools sÃ³ aparecem na inicializaÃ§Ã£o).

## PrÃ³ximos passos possÃ­veis

- `eco-knowledge` e `eco-obsidian` poderiam ser fundidos ou o bridge poderia usar
  `search-vault` proativamente para incluir contexto relevante no prompt.
- File watcher em `conhecimento/` para invalidar cache do estado quando notas mudam.

## Conexoes

- [[2026-07-27-teste-do-vigilante-automático-teste-do-sistema-de]]