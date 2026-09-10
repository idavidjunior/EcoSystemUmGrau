# 2026-09-10 - Ciclo 8 - ADR-008: Arquitetura do Produto Integrado (Quadro de Notas com IA)

**Categoria:** decisao
**Contexto:** O Ciclo 8 do roadmap de capacitação web exige um micro-produto completo que integre as camadas validadas nos ciclos 1-7 (servidor, API, WS, sqlite, IA, segurança, performance) em um único produto real, com pelo menos 20 demonstrações/evidências. A stack do roadmap (ADR-003/004/005/006/007) é Python stdlib + websockets + sqlite + playwright.
**Projeto:** EcoSystemUmGrau

## Decisão

Construir o **Quadro de Notas com IA** como produto integrado: um servidor HTTP único (`server.py`) com rotas CRUD de notas (REST), chat via IA do cognitive_core (`/api/chat`), e estado em sqlite persistente. O frontend `index.html` consome tudo (fetch + WebSocket em `/ws`). WebSocket roda em loop asyncio **separado** do pump HTTP (`ws_broadcast.py`), usado só para broadcast de eventos (`nota_criada`, `nota_atualizada`, `nota_excluida`) — comunicação publish/subscribe pura, sem solicitar estado do cliente. Reutiliza o contrato da `SecurityMiddleware` do Ciclo 6 (headers OWASP, rate limit, content-type check, sanitização, tratamento de erros).

## Alternativas consideradas

1. **Alternativa A — WebSocket dentro do mesmo servidor HTTP (handler + upgrade inline)**: mistura flows async com HTTP sync do ThreadingHTTPServer; complica shutdown e vida útil de sockets; não seguir por ADR-003 (stdlib).
2. **Alternativa B — WS integrado ao event loop do ThreadingHTTPServer**: inviável (ThreadingHTTPServer é sync); suportaria apenas 1 cliente em poll.
3. **Alternativa C — dois processos separados (HTTP e ws_broadcast como serviço)**: mais robusto para prod, mas desnecessário para o micro-produto; um único emissor em endpoint /ws já cobre o requisito.

## Por quê

Escolhi manter o WS em thread asyncio daemon própria, separada do servidor HTTP sync. Isso preserva o padrão do Ciclo 3 (websockets 17 + asyncio, ADR-004), evita trava de shutdown (evento `_PARADA` + `run_until_complete` termina na hora) e mantém `emitir()` thread-safe via `run_coroutine_threadsafe`. O `parar()` precisa aguardar a thread (join) antes de permitir novo start, senão a porta WS nova pode colidir com o socket antigo.

## Evidência

Produto validado com 27 checks OK (0 falhas) em `labs/ciclo-8-produto-quadro-notas`. CWV dentro das bandas Good (LCP 692ms, CLS 0.000, INP 0ms) medido em `benchmarks/ciclo-8-cwv.json`. Bloco N (produto integrado) promovido a MASTERED no mapa de competências (`conhecimento/web/README.md`).

**Projeto:** EcoSystemUmGrau