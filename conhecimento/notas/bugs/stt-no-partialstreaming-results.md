---
tags: [bug, ecosistema-opencode, incremental, parameter, reporting, segment]
aliases: [STT no partial/streaming results]
date: 2026-08-07
---

# STT no partial/streaming results

**Projeto:** ecosistema-opencode

## Causa Raiz
_stt_whisper joined all Whisper segments at once; onPartialResults callback in VoxStt.kt was empty

## Correcao
Added partial_callback parameter to _stt_whisper for incremental segment reporting; implemented onPartialResults in VoxStt.kt to forward partial text to UI
## Conexoes

- [[2026-07-27-fallback-automático-de-modelo-llm-com-bun-razrooo]]
- [[2026-07-27-sistema-automático-de-captura-de-conhecimento-do-]]
- [[bug-hub-bugs]]
- [[cluster-hub-ecossistema]]
- [[ensureserve-spawns-opencode-serve-without-passing-env-contex]]
- [[http-401-unauthorized-on-session-and-globalsessions]]