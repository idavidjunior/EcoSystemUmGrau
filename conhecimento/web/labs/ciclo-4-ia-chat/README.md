# Ciclo 4 — IA como Interface Web

**Status:** VALIDADO (2026-09-09) — `test_ia_chat.py` → `STATUS: OK (11 checks, 0 falhas)`

## Objetivo

Provar bloco H (IA/LLM aplicada em web): um navegador conversa com um **agente real** do ecossistema. O servidor HTTP (stdlib, ADR-003) expõe `POST /api/chat`; o handler chama `scripts.cognitive_core.process_user_input` — o orquestrador cognitivo real (mesma função que o Jarvis usa). O chat HTML consome o endpoint com `fetch` e exibe `resposta` + intenção + modelo.

## Como usar

```bash
python server.py          # chat: http://127.0.0.1:8094
python test_ia_chat.py    # validação (11 checks)
```

## Rotas

- `GET /` — chat HTML/JS (fetch para /api/chat)
- `GET /api/health` — health
- `POST /api/chat` — `{"mensagem": "...", "session_id": "...", "contexto": {...}}` → `{"resposta", "intent", "summary"}`
- `GET /api/explode` — erro 500 forçado (teste adversarial)

## Validação executada

| Check | Resultado |
|---|---|
| GET / index.html com fetch | PASS |
| health ok | PASS |
| POST /api/chat conversa real (cognitive_core) | PASS |
| session custom | PASS |
| sem mensagem → 400 | PASS |
| mensagem vazia → 400 | PASS |
| JSON inválido → 400 | PASS |
| GET em /api/chat → 405 | PASS |
| rota inexistente → 404 | PASS |
| PUT → 405 | PASS |
| /api/explode → 500 | PASS |

## Aprendizados

1. `process_user_input(user_input, contexto, session_id)` é a interface pública estável do cognitive_core (retorna `response` + `summary`); reutilizá-la — não reimplementar orquestração.
2. Importar `scripts.*` do lab exige a raiz do projeto no `sys.path` (5 níveis acima de `ciclo-4-ia-chat/`).
3. Foi corrigido um bug real no cognitive_core: o contrato de `_get_memory_context` retornava `str`, mas o fluxo esperava `dict` (`str` sem `.get`/`.update`). Normalizado tanto em `execute_cognitive_cycle` (contexto) quanto em `_execute_conversation_flow` (memórias) — ver `conhecimento/aprendizados/`.