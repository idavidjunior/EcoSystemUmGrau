---
tags: [automaticamente, decisao, espelho, opencode, reflete, vivo]
aliases: [vault obsidian fonte viva]
date: 2026-08-08
---

# vault obsidian fonte viva

**Fonte:** opencode

---
tipo: decisao
tags: [obsidian, widget, grafo, arquitetura, tags-semanticas, rake]
data: 2026-08-02
contexto: Reestruturacao do pipeline de geracao do grafo — Obsidian vira cerebro vivo, widget espelho
decisao: generate-graph-html.py agora le o vault Obsidian (conhecimento/notas/*.md) em vez de knowledge_graph.json. O widget_grafo.py chama Bridge.regenerar() quando a versao detecta mudança no vault. Smart Connections (plugin Obsidian) cria [[wikilinks]] semanticos que o widget reflete automaticamente.
impacto: Cérebro único: Obsidian organiza + conecta; widget mostra a organização viva. Zero duplicação de grafos.

## Tags semanticas na origem (RAKE leve, stdlib puro)

Para conectar pontos isolados, o enriquecimento acontece na ORIGEM, em 3 camadas:

1. **`knowledge_consolidator.register_learning_file`**: `learning["tags"]` agora recebe
   `[cat, "opencode"] + extrair_tags(titulo + contexto + texto[:300])` via
   `scripts/semantic_tags.py` (sys.path com `..\..\scripts`). Essas tags propagam para
   `knowledge_graph.json` → `mission_learnings[].tags`.
2. **`generate-obsidian-notes.py`**: cada nota do vault ganha `_enriquecer_tags()` que
   soma até 4 tags RAKE do `title + body` ao frontmatter `tags:` — são essas tags que o
   Smart Connections usa para embeddings semânticos.
3. **`memory_engine.add_memory`**: `memories.json` agora auto-extrai até 6 tags RAKE de
   `task + summary`.

Fluxo completo: `conhecimento/aprendizados/*.md` → `knowledge_graph.json` (tags
semânticas) → `generate-obsidian-notes.py` → vault `conhecimento/notas/*.md` (frontmatter
enriquecido) → `generate-graph-html.py` lê vault → `grafo.html` + widget.

`semantic_tags.py` é **stdlib puro** (RAKE leve, PT/EN stopwords) — sem keybert/sklearn/
sentence-transformers, que não estão instalados (apenas torch). Determinístico e offline.

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]