---
tags: [moc, conhecimento]
---

# Mapa — Conhecimento

## Visão Geral

```dataview
TABLE length(rows) as Total
FROM "conhecimento/notas"
GROUP BY split(file.folder, "/")[2] as Tipo
SORT Tipo ASC
```

## Últimas Adições
```dataview
TABLE file.cday as Data
FROM "conhecimento/notas"
SORT file.cday DESC
LIMIT 20
```

## Base Exportada (contexto dos agentes)
- [[ler-runtime/CONHECIMENTO.md]]
- [[ler-runtime/knowledge/knowledge_graph.json]]
