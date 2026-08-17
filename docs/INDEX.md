---
tags: [index, ecossistema]
---

# EcoSystemUmGrau — Mapa Vivo do Conhecimento

> Tudo gerado automaticamente pelo ecossistema. Nada escrito à mão.
> Última atualização: `= date(today)`

## Projetos Monitorados

`= this.file.folder`

```dataview
TABLE rows.file.link as Arquivos
FROM "conhecimento/notas"
GROUP BY split(file.folder, "/")[2] as Categoria
SORT Categoria ASC
```

## Últimos Aprendizados

```dataview
TABLE file.cday as Data, file.etags as Tags
FROM "conhecimento/aprendizados"
SORT file.cday DESC
LIMIT 10
```

## Conhecimento por Tipo

### Padrões Técnicos
```dataview
TABLE source as Fonte
FROM "conhecimento/notas/padroes"
SORT file.name ASC
```

### Decisões
```dataview
TABLE source as Fonte
FROM "conhecimento/notas/decisoes"
SORT file.name ASC
```

### Bugs Corrigidos
```dataview
TABLE source as Projeto
FROM "conhecimento/notas/bugs"
SORT file.name ASC
```

### Heurísticas
```dataview
TABLE domain as Dominio
FROM "conhecimento/notas/heuristicas"
SORT file.name ASC
```

### Padrões Cognitivos
```dataview
TABLE domain as Dominio
FROM "conhecimento/notas/cognitivo"
SORT file.name ASC
```

### Frameworks
```dataview
TABLE description as Descricao
FROM "conhecimento/notas/frameworks"
SORT file.name ASC
```

### Missões (LER)
```dataview
TABLE status as Status, file.cday as Data
FROM "conhecimento/notas/missoes"
SORT file.cday DESC
LIMIT 15
```

## Tags

```dataview
TABLE rows.file.link as Notas
FROM "conhecimento/notas"
FLATTEN file.tags as Tag
GROUP BY Tag
SORT Tag ASC
```

---
> **Atalhos:** `Ctrl+P` palette | `Ctrl+O` switcher | `Ctrl+Shift+T` template | `Ctrl+Shift+S` git | `Ctrl+Shift+G` graph
