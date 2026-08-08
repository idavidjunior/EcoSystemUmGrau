---
tags: [bug, child, ecosistema-opencode, password, process, propagated]
aliases: [_ensure_serve() spawns opencode serve without passing env co]
date: 2026-08-08
---

# _ensure_serve() spawns opencode serve without passing env context

**Projeto:** ecosistema-opencode

## Causa Raiz
asyncio.create_subprocess_exec inherits parent env, but explicit env ensures correct OPENCODE_SERVER_PASSWORD is propagated to serve child process

## Correcao
Added env={**os.environ} to _ensure_serve() and _ensure_serve_global() in jarvis_bridge.py; run_serve.py now loads .env and passes env explicitly
## Conexoes

- [[2026-07-27-fallback-automático-de-modelo-llm-com-bun-razrooo]]
- [[2026-07-27-sistema-automático-de-captura-de-conhecimento-do-]]
- [[bug-hub-bugs]]
- [[cluster-hub-ecossistema]]
- [[geraraudio-blocks-until-full-tts-generation-no-streaming]]
- [[http-401-unauthorized-on-session-and-globalsessions]]