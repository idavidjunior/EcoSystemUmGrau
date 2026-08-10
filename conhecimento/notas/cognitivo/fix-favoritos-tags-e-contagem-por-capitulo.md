---
tags: [adicionar, capítulo, cognitivo, defensiva, general, migração]
aliases: [fix favoritos tags e contagem por capitulo]
date: 2026-08-09
---

# fix favoritos tags e contagem por capitulo

**Dominio:** general

---
tipo: erro
tags: [biblia, favoritos, sqlite, schema, migracao, contagem, capitulo]
data: 2026-08-09
contexto: Bug de favoritos reportado pelo usuário + pedido de contagem de favoritos/notas por capítulo
decisao: Renomear coluna `tag` para `tags` no banco pré-populado e adicionar migração defensiva; reativar spinner de capítulos com contagens; marcar versículo favoritado com ★
impacto: Favoritos voltaram a funcionar; capítulos mostram quantos versículos estão favoritados e quantas notas exist
## Conexoes

- [[cluster-hub-cognicao]]
- [[cognitivo-hub-cognitivo]]