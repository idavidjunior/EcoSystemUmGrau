# Ciclo 3 — Realtime WebSocket (blocos F/H)

**Status:** VALIDADO
**Data:** 2026-09-08
**Mapa:** bloco F → VALIDATED/3 (estendido com WS); bloco H → VALIDATED/3
**Stack:** websockets 17.0.1 (asyncio server) + estado persistente do runtime (`runtime/state.json`)

## Entrega

Servidor WebSocket em `ws_server.py` com três rotas:

- `/echo` — eco de mensagem JSON (`tipo: eco`) e resposta de erro para JSON inválido (`tipo: erro`).
- `/broadcast` — registra clientes e repassa cada mensagem a todos os demais conectados (`tipo` preservado, com `origem: broadcast`).
- `/estado` — heartbeat (ping → pong com hora em UTC) e snapshot do estado persistente do runtime (`projeto_ativo`, `objetivo`, `ultima_tarefa`, `last_task`).

Rotas fora do conjunto `/echo`, `/broadcast`, `/estado` são fechadas com código 1008 (policy violation).

## Como validar

```
python conhecimento/web/labs/ciclo-3-websocket/test_ws.py
```

## Resultado

```
[PASS] echo
[PASS] echo json inválido
[PASS] broadcast para outro cliente
[PASS] heartbeat ping/pong
[PASS] estado persistente do runtime - projeto=JunkScanner
[PASS] rota inexistente rejeitada
STATUS: OK (6 checks, 0 falhas)
```

## Notas de arquitetura

- `websockets.asyncio.server.serve(handler, host, port)` + handler único com roteamento por `websocket.request.path`.
- Thread daemon para teste; `parar()` encerra via `asyncio.Event` para shutdown ordenado do loop.
- Path do estado: o teste injeta `ws_server.ESTADO_PATH` apontando para `runtime/state.json` do repositório.

## Decisão

ADR-004 (`conhecimento/web/adrs/2026-09-08-adr-004-websocket-realtime.md`): websockets 17 como camada WS; aiohttp fica como alternativa para HTTP+WS combinados; uvicorn puro permanece adiado para Ciclos 4+.