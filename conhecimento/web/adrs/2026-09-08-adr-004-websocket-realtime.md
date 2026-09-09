# 2026-09-08 - Decisão da camada WebSocket realtime — websockets + estado do runtime

**Categoria:** decisao
**Contexto:** Missão de capacitação web do ecossistema (13 fases; FASES 1–3 entregues). O Ciclo 3 (Realtime WebSocket) exige eco, broadcast, heartbeat e integração com o estado persistente do runtime. O teste canônico validou tudo: `test_ws.py` → `STATUS: OK (6 checks, 0 falhas)` (bloco F estendido; bloco H = VALIDATED). Ciclo 2 decidiu stdlib para rotas HTTP (ADR-003); falta fixar a camada de tempo real.
**Projeto:** EcoSystemUmGrau

## Decisão

Usar **websockets 17.0.1** (asyncio server) como camada WebSocket do ecossistema web, com roteamento por `request.path` em handler único e integração com `runtime/state.json` via rota `/estado` (heartbeat ping/pong + snapshot). **aiohttp** fica documentado como alternativa para cenários de HTTP+WS no mesmo servidor; **uvicorn puro** permanece adiado para os Ciclos 4+ (async/WebSocket em produção), e **FastAPI** continua fora.

## Alternativas consideradas

1. **Alternativa A — websockets 17 puro** — foco único em WS, API asyncio limpa, validado com 6/6 checks (eco, broadcast, heartbeat, estado, rota inválida com close 1008).
2. **Alternativa B — aiohttp (HTTP+WS num servidor)** — útil quando um único server servir HTTP e WS; ainda não necessário, pois HTTP segue em stdlib (ADR-003).

## Por quê

O Ciclo 3 entregou evidência real com websockets puro e cliente de teste real, incluindo broadcast e heartbeat. Pelo princípio da mudança mínima segura e REUTILIZAR > ADAPTAR > ESTENDER > CRIAR, a camada WS é dedicada (websockets) enquanto HTTP permanece em stdlib; unificar em aiohttp só quando houver necessidade real de HTTP+WS no mesmo processo.