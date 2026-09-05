---
tags: [causando, chamar, cognitivo, general, ondowngrade, tenta]
aliases: [crash topicindex version mismatch]
date: 2026-08-20
---

# crash topicindex version mismatch

**Dominio:** general

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
2. Popular tabela `t
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]