---
tags: [bíblia, bíblicos, cognitivo, estudo, general, visível]
aliases: [crash topicindex version mismatch]
date: 2026-08-23
---

# crash topicindex version mismatch

**Dominio:** general

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

Incompatibilidade de versão entre o banco `indic
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]