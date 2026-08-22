---
tags: [bug, ecosistema-opencode, incremental, parameter, reporting, segment]
aliases: [STT no partial/streaming results]
date: 2026-08-22
---

# STT no partial/streaming results

**Projeto:** ecosistema-opencode

## Causa Raiz
_stt_whisper joined all Whisper segments at once; onPartialResults callback in VoxStt.kt was empty

## Correcao
Added partial_callback parameter to _stt_whisper for incremental segment reporting; implemented onPartialResults in VoxStt.kt to forward partial text to UI
## Conexoes

- [[bug-hub-bugs]]
- [[cluster-hub-ecossistema]]
- [[ensureserve-spawns-opencode-serve-without-passing-env-contex]]
- [[geraraudio-blocks-until-full-tts-generation-no-streaming]]
- [[http-401-unauthorized-on-session-and-globalsessions]]
- [[pronuncia-do-nome-do-usuario-david-deivid]]