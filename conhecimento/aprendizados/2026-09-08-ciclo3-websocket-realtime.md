---
tipo: padrao
tags: [engenharia-web, websocket, realtime, broadcast, heartbeat, asyncio, adr]
data: 2026-09-08
contexto: Missão de capacitação web — Ciclo 3 (Realtime WebSocket, blocos F/H) encerrado com validação real (test_ws.py: STATUS OK, 6 checks, 0 falhas; eco, broadcast, heartbeat, estado persistente e rota inválida 1008) e ADR-004 registrado.
decisao: Usar websockets 17 (asyncio server) como camada WS do ecossistema, com handler único roteado por request.path e integração com runtime/state.json via rota /estado; aiohttp fica como alternativa de HTTP+WS combinados; shutdown ordenado via asyncio.Event em thread daemon.
impacto: Blocos F/H = VALIDATED/3; ADR-004 registrado; base pronta para o Ciclo 4 (IA como interface web).
---

# Ciclo 3 — Realtime WebSocket (eco, broadcast, heartbeat, estado)

## O que foi validado

- `python conhecimento/web/labs/ciclo-3-websocket/test_ws.py` → `STATUS: OK (6 checks, 0 falhas)`.
- `/echo`: eco de JSON (`tipo: eco`) e erro para JSON inválido (`tipo: erro`).
- `/broadcast`: cliente A envia, cliente B recebe com `origem: broadcast` e `tipo` preservado.
- `/estado`: ping → pong (com hora UTC) e snapshot do runtime (`projeto_ativo=JunkScanner`, `objetivo`, `ultima_tarefa`, `last_task`).
- Rota fora de `/echo|/broadcast|/estado` → close 1008 (policy violation).

## Padrão consolidado

- `websockets.asyncio.server.serve(handler, host, port)` + handler único; roteamento por `websocket.request.path`.
- Thread daemon com `asyncio.new_event_loop()` + `asyncio.Event` global para shutdown ordenado (`parar()`); teste chama `parar()` e `join` no lugar de `loop.stop()` bruto (evita "Event loop closed" e corrotinas órfãs).
- Estado persistente injetado no servidor via módulo (`ws_server.ESTADO_PATH`) apontando para `runtime/state.json`.

## Próximo

Ciclo 4 — IA como interface web: endpoint POST que conversa com cognitive_core/agents; PRÉ-REQUISITO: corrigir timeout da busca MCP (-32603) antes de RAG.
