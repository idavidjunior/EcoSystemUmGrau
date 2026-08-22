---
tags: [bug, done, ecosistema-opencode, messages, playback, progressive]
aliases: [gerar_audio() blocks until full TTS generation, no streaming]
date: 2026-08-22
---

# gerar_audio() blocks until full TTS generation, no streaming

**Projeto:** ecosistema-opencode

## Causa Raiz
gerar_audio accumulated all edge-tts chunks into single base64 before sending to client; no incremental audio delivery

## Correcao
Added gerar_audio_stream() async generator yielding base64 chunks incrementally; modified ws_responder to send audio_streaming/audio_chunk/audio_done messages for progressive playback
## Conexoes

- [[bug-hub-bugs]]
- [[cluster-hub-ecossistema]]
- [[ensureserve-spawns-opencode-serve-without-passing-env-contex]]
- [[http-401-unauthorized-on-session-and-globalsessions]]
- [[pronuncia-do-nome-do-usuario-david-deivid]]
- [[stt-no-partialstreaming-results]]