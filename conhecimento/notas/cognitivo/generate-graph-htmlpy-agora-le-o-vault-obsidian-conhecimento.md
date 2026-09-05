---
tags: [automaticamente, cognitivo, espelho, general, reflete, vivo]
aliases: [generate-graph-html.py agora le o vault Obsidian (conhecimen]
date: 2026-09-05
---

# generate-graph-html.py agora le o vault Obsidian (conhecimento/notas/*

**Dominio:** general

Tipo: decisao

Tags: [obsidian, widget, grafo, arquitetura]

Data: 2026-08-02

contexto: Reestruturacao do pipeline de geracao do grafo — Obsidian vira cerebro vivo, widget espelho

decisao: generate-graph-html.py agora le o vault Obsidian (conhecimento/notas/*.md) em vez de knowledge_graph.json. O widget_grafo.py chama Bridge.regenerar() quando a versao detecta mudança no vault. Smart Connections (plugin Obsidian) cria [[wikilinks]] semanticos que o widget reflete automaticamente.

impacto: Cére

## O problema

O "Obsidian" do ecossistema é uma estrutura de pastas com markdown:

- `docs/` (3 notas: arquitetura, auditoria, ecossistema)
- `conhecimento/` (327 notas: aprendizados, decisões, cognitivo)
- `documentos/` (0 notas)

A bridge (`jarvis_bridge.py`) só expunha a **contagem** de arquivos ao LLM
("Total vault: 330 notas"). O LLM sabia que existiam, mas nunca lia o conteúdo.
A busca semântica (`eco-knowledge` / `search`) cobria `CONHECIMENTO.md`,
`memories.json` e o knowledge graph — mas **não** os 327 arquivos `conhecimento/`.

## A solução

Criado `scripts/mcp-obsidian-server.py` — Python puro, JSON-RPC 2.0 via stdio,
mesmo padrão do `mcp-knowledge-server.py`.

### Tools expostas

| Tool | Descrição |
|------|-----------|
| `list-vault` | Lista diretórios e arquivos .md do vault (recursivo opcional) |
| `read-note` | Lê conteúdo de uma nota .md (com offset/limit) |
| `search-vault` | Busca BM25 simples no conteúdo de todas as notas |
| `vault-summary` | Estatísticas: total 
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]