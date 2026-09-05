---
tags: [decisao, estavam, memoria, nativos, opencode, tools]
aliases: [remocao mcps node inoperantes]
date: 2026-09-05
---

# remocao mcps node inoperantes

**Fonte:** opencode

## Contexto

Quatro servidores MCP do opencode (filesystem, search, terminal, github) estavam
desligados desde sempre: rodam via `node mcp-servers/<nome>/index.js`, mas o Node.js
nao esta instalado no PC (nao existe `node.exe` no PATH nem em locais padrao). O erro
de inicializacao era WinError 2 (sistema nao encontra o arquivo). Os outros 12 MCPs
funcionam porque sao Python puro e o Python esta no PATH.

## Analise

Inspecao dos 4 servidores Node mostrou redundancia total com capacidades ja existentes:

- filesystem (listar/ler/escrever/pesquisar arquivos) duplica os tools nativos
  Read/Write/Edit/Glob/Grep do opencode e o mcp-dev-tools.
- terminal (PowerShell com bloqueio de destrutivos) duplica o Bash nativo do opencode.
- search (BM25 sobre knowledge graph, CONHECIMENTO.md, memories, habilidades,
  aprendizados e notas) duplica eco-knowledge, eco-obsidian e mcp-memoria (Python,
  ja online).
- github (wrapper do CLI gh) duplica o uso do gh via persistencia.ps1 e Composio.

Nenhum d
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]