---
tags: [block, bug, catch, cleanup, ecosistema-opencode, safe]
aliases: [VoxAudioPlayer temp file leak on exception]
date: 2026-08-11
---

# VoxAudioPlayer temp file leak on exception

**Projeto:** ecosistema-opencode

## Causa Raiz
tempFile variable was scoped inside try block; if exception before MediaPlayer setup, tempFile was orphaned; stop() before play() could leave old tempFile undeleted

## Correcao
Promoted tempFile to function scope with null-safe cleanup in catch block; VoxAudioPlayer.kt now uses var tempFile: File? = null and deletes in all error paths
## Conexoes

- [[2026-07-27-fallback-automático-de-modelo-llm-com-bun-razrooo]]
- [[2026-07-27-sistema-automático-de-captura-de-conhecimento-do-]]
- [[bug-hub-bugs]]
- [[cluster-hub-ecossistema]]
- [[http-401-unauthorized-on-session-and-globalsessions]]
- [[pronuncia-do-nome-do-usuario-david-deivid]]