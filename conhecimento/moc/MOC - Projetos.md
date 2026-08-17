---
tags: [moc, projetos]
---

# Mapa — Projetos

## Android
```dataview
TABLE rows.file.link as Notas
FROM "conhecimento/notas/bugs"
GROUP BY source as Projeto
SORT Projeto ASC
```

## Bugs por Projeto
```dataview
TABLE root_cause as Causa, fix as Correcao
FROM "conhecimento/notas/bugs"
SORT file.name ASC
```

## Habilidades Disponíveis (40)
Veja [[mcp/manifesto_mcp.json]]
