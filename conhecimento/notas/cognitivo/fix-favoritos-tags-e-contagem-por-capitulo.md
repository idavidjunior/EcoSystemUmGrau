---
tags: [boot, cognitivo, fallback, general, quebrava, vigor]
aliases: [fix favoritos tags e contagem por capitulo]
date: 2026-08-09
---

# fix favoritos tags e contagem por capitulo

**Dominio:** general

## Contexto

O banco pré-populado `assets/databases/biblia_estudo.db` tinha a tabela `favorites` com coluna `tag` (singular),
mas o código (`FavoriteDao.insert` e `cursorToFavorite`) usava `tags` (plural). Como o banco é copiado de assets
e não criado via `onCreate` do helper, o schema real era o do assets → o `INSERT` falhava silenciosamente e o
favorito nunca era salvo nem marcado.

## Decisão

1. **Assets**: `ALTER TABLE favorites RENAME COLUMN tag TO tags;` (sqlite3 3.50.6).
2. **Migração defensiva** no `DatabaseManager.migrateBibleDatabase`: se a coluna `tags` não existir,
   `ADD COLUMN tags TEXT` + `UPDATE favorites SET tags = tag WHERE tag IS NOT NULL` — cobre dispositivos
   que já copiaram o banco antigo (sem precisar bumpar CURRENT_DB_VERSION nem apagar dados).
3. **Contagem por capítulo**: `FavoriteDao.getCountByChapter(bookId, chapter)` e
   `NoteDao.getCountByChapter(bookId, chapter)`.
4. **Seletor de capítulos**: o `chapterSpinner` estava `visibility="gone"` no layout. R

---
tipo: erro
tags: [config, opencode, preflight, llm_model, template]
data: 2026-08-09
contexto: "@sync - preflight falhou com 'Secrets: env LLM_MODEL AUSENTE'"
decisao: >
  O commit 323a3879 trocou o placeholder "{{LLM_MODEL}}" por "{env:LLM_MODEL}"
  no template config/opencode.jsonc, MAS o setup-auto.ps1 continua renderizando
  "{{LLM_MODEL}}" (Replace com chaves duplas). Como nunca houve match, o deployed
  manteve "{env:LLM_MODEL}" literal e o preflight passou a exigir a env var
  LLM_MOD

---
tipo: erro
tags: [opencode, config, llm, placeholder, model_not_found, eco-system, sync]
data: 2026-08-09
contexto: Ao trocar de LLM, contextos, tarefas e projetos deixaram de ser reconhecidos em sessoes novas. Investigacao revelou que o placeholder {{LLM_MODEL}} no config de opencode NAO e substituido pelo opencode, gerando model_not_found que quebrava o boot das sessoes novas (sem fallback em vigor).
decisao: Substituir o placeholder nao-resolvivel por {env:LLM_MODEL} (mecanismo nativo de 
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]