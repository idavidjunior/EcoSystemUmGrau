---
tipo: erro
tags: [biblia, favoritos, sqlite, schema, migracao, contagem, capitulo]
data: 2026-08-09
contexto: Bug de favoritos reportado pelo usuário + pedido de contagem de favoritos/notas por capítulo
decisao: Renomear coluna `tag` para `tags` no banco pré-populado e adicionar migração defensiva; reativar spinner de capítulos com contagens; marcar versículo favoritado com ★
impacto: Favoritos voltaram a funcionar; capítulos mostram quantos versículos estão favoritados e quantas notas existem
---

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
4. **Seletor de capítulos**: o `chapterSpinner` estava `visibility="gone"` no layout. Reativado (`visible`) e
   cada item agora mostra `Capítulo N ★X 📝Y` quando há favoritos/notas. Removido o `btnChapterTitle` estático.
5. **Marca visual**: no leitor, versículo favoritado exibe `★` junto ao número (via `getVerseNumbersByChapter`).
6. **Atualização**: `refreshChapterSpinner()` no `onResume`, ao favoritar/desfavoritar e após salvar nota.

## Validação

- Favoritar Gênesis 1:1 → número do versículo passou a mostrar `1★` e o seletor mostrou `Capítulo 1 ★1`.
- Dropdown do spinner lista todos os capítulos; só os com conteúdo exibem contagens.
- Compilado com `.\build.ps1`, instalado via adb, sem crash no logcat.

## Impacto

- Bug de favoritos corrigido para instalações novas (assets corrigido) e existentes (migração em runtime).
- Contagens por capítulo visíveis no seletor do leitor.
- Padrão: quando o banco é pré-populado de assets, o schema de `assets/databases/*.db` é a fonte da verdade;
  sempre conferir o schema real antes de assumir o do `onCreate`.
