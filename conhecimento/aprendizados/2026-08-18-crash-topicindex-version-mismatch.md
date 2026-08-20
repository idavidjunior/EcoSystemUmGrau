---
tipo: erro
tags: [android, sqlite, crash, database, version-mismatch]
data: 2026-08-18
contexto: TopicIndexActivity crashava ao abrir o Índice Temático no app Bíblia de Estudo
decisao: Corrigir DATABASE_VERSION de 1 para 2 no TopicIndexDatabaseHelper
impacto: Crash resolvido, Índice Temático agora funciona com 56 tópicos bíblicos
---

## Problema

TopicIndexActivity crashava imediatamente ao abrir, sem mensagem de erro visível.

## Causa raiz

Incompatibilidade de versão entre o banco `indices.db` (asset) e o `TopicIndexDatabaseHelper`:

- `indices.db` nos assets tinha `PRAGMA user_version = 2`
- `TopicIndexDatabaseHelper` declarava `DATABASE_VERSION = 1`

Quando `SQLiteOpenHelper.getWritableDatabase()` detecta que a versão do arquivo (2) é maior que a versão do helper (1), ele tenta chamar `onDowngrade()`. Como `TopicIndexDatabaseHelper` não sobrescreve esse método, a implementação padrão lança `SQLiteException`, causando o crash.

## Diagnóstico

1. Verificar schema do banco: `PRAGMA user_version` e `PRAGMA table_info(topics)`
2. Comparar com o código do DatabaseHelper
3. Identificar que `topics` existia mas estava vazia (0 registros)
4. O crash não era por dados vazios, mas por falha na abertura do banco

## Solução

1. Alterar `DATABASE_VERSION` de 1 para 2 em `TopicIndexDatabaseHelper.java`
2. Popular tabela `topics` com 56 tópicos bíblicos via script Python
3. Incrementar `CURRENT_DB_VERSION` de 9 para 10 em `DatabaseManager` para forçar re-cópia

## Verificação

- App compilado com 87 arquivos Java
- APK instalado via script resiliente
- Índice Temático abre sem crash
- 56 tópicos exibidos corretamente

## Padrão para futuros projetos

Sempre garantir que `DATABASE_VERSION` no `SQLiteOpenHelper` seja >= ao `user_version` do banco pré-populado nos assets. Se o banco é criado externamente (Python, SQL editor), definir `PRAGMA user_version=N` antes de incluir como asset.
