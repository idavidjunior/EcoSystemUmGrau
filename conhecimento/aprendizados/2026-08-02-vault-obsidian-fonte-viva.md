---
tipo: decisao
tags: [obsidian, widget, grafo, arquitetura]
data: 2026-08-02
contexto: Reestruturacao do pipeline de geracao do grafo — Obsidian vira cerebro vivo, widget espelho
decisao: generate-graph-html.py agora le o vault Obsidian (conhecimento/notas/*.md) em vez de knowledge_graph.json. O widget_grafo.py chama Bridge.regenerar() quando a versao detecta mudança no vault. Smart Connections (plugin Obsidian) cria [[wikilinks]] semanticos que o widget reflete automaticamente.
impacto: Cérebro único: Obsidian organiza + conecta; widget mostra a organização viva. Zero duplicação de grafos.
