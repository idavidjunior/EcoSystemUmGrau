# Ciclo 2 — Backend estruturado (rotas, status codes, erros JSON)

**Status:** VALIDADO
**Data:** 2026-09-08
**Mapa:** bloco F → VALIDATED/3 (ADR-003)

## Entrega

Mini-API Python stdlib (`ThreadingHTTPServer`) em `server.py` com rotas múltiplas, parâmetros via query string, status codes corretos e erros JSON.

Rotas: `/` (200), `/api/health` (200), `/api/soma?a=2&b=3` (200), `/api/items` (200), `/api/items/7` (200), `/api/items/abc` (404), POST `/api/items` (201/400), DELETE `/api/items/3` (200), PUT (405), rota inexistente (404), `/api/explode` (500).

## Como validar

```
python conhecimento/web/labs/ciclo-2-backend-estruturado/test_server.py
```

## Resultado

```
[PASS] GET / raiz
[PASS] GET /api/health
[PASS] GET /api/soma 2+3
[PASS] GET /api/soma param inválido
[PASS] GET /api/items
[PASS] GET /api/items/7
[PASS] GET /api/items/abc 404
[PASS] POST /api/items 201
[PASS] POST sem nome 400
[PASS] POST json inválido 400
[PASS] DELETE /api/items/3
[PASS] PUT /api/items/3 405
[PASS] GET rota inexistente 404
[PASS] GET /api/explode 500
STATUS: OK (14 checks, 0 falhas)
```

## Decisão de arquitetura

ADR-003 (`conhecimento/web/adrs/2026-09-08-adr-003-backend-estruturado.md`): manter/estender `ThreadingHTTPServer` stdlib; uvicorn puro documentado para Ciclos 4+; FastAPI fora.

## Aprendizado consolidado

`conhecimento/aprendizados/2026-09-08-ciclo2-backend-estruturado.md` — inclui o pitfall da correção de indentação via escrita atômica quando o tool edit envia par idêntico.