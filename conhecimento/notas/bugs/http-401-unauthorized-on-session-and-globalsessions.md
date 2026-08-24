---
tags: [4216, bug, correct, ecosistema-opencode, new, pid]
aliases: [HTTP 401 Unauthorized on /session and /global/sessions/*]
date: 2026-08-07
---

# HTTP 401 Unauthorized on /session and /global/sessions/*

**Projeto:** ecosistema-opencode

## Causa Raiz
opencode serve was started with OPENCODE_SERVER_PASSWORD=521cf1f4-... (Windows user env var) but .env was updated to edbe7432-... and serve was never restarted

## Correcao
Updated Windows HKCU env var to match .env password, killed stale serve (PID 4724), started new serve (PID 4216) with correct password
## Conexoes

- [[bug-hub-bugs]]
- [[cluster-hub-ecossistema]]
- [[ensureserve-spawns-opencode-serve-without-passing-env-contex]]
- [[geraraudio-blocks-until-full-tts-generation-no-streaming]]
- [[pronuncia-do-nome-do-usuario-david-deivid]]
- [[stt-no-partialstreaming-results]]