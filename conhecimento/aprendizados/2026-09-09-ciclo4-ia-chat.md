---
tipo: padrao
tags: [engenharia-web, ia, cognitive-core, chat, fetch, bloco-h, stdlib]
data: 2026-09-09
contexto: Missão de capacitação web — Ciclo 4 (IA como interface web, bloco H) encerrado com validação real (test_ia_chat.py: STATUS OK, 11 checks, 0 falhas; chat HTML/JS consumindo POST /api/chat ligado ao process_user_input do cognitive_core real). ADR-003 mantido (HTTP stdlib).
decisao: Expor o cognitive_core como interface web via POST /api/chat com ThreadingHTTPServer, chamando process_user_input(mensagem, contexto, session_id) e devolvendo resposta + intent + summary; HTML/JS do lado cliente usa fetch. Import de scripts.* exige a raiz do projeto no sys.path (5 níveis acima da pasta do lab).
impacto: Bloco H = VALIDATED/3 com chat web real ao agente do ecossistema; roadmap Ciclo 4 concluído; RAG continua pendente (timeout MCP -32603).
---

# Ciclo 4 — IA como interface web (chat ligado ao cognitive_core)

## O que foi validado

- `python conhecimento/web/labs/ciclo-4-ia-chat/test_ia_chat.py` → `STATUS: OK (11 checks, 0 falhas)`.
- `GET /` serve o chat HTML (JS consome `/api/chat` via fetch); `GET /api/health` retorna status ok.
- `POST /api/chat` conversa com o agente real: `{"mensagem": "explique o que e um servidor HTTP"}` → `{"resposta": ..., "intent": ..., "summary": ...}`.
- Adversarial: sem mensagem → 400; mensagem vazia → 400; JSON inválido → 400; GET/PUT em `/api/chat` → 405; rota inexistente → 404; `/api/explode` → 500.

## Padrão consolidado

- Reutilizar `scripts.cognitive_core.process_user_input` como a única porta de entrada pública da orquestração cognitiva — nunca reimplementar o ciclo (intent → router → council → validação).
- Servidor: `ThreadingHTTPServer` (ADR-003) com helpers `_json`/`_erro`/`_html`/`_rota`/`_ler_corpo`, rota única por `self.path.split("?",1)[0]`.
- `process_user_input` pode envolver LLM router/memória → teste usa timeout de 90s no request da IA (e 10s no resto).
- Importar `scripts.*` de dentro de um lab exige `sys.path.insert(0, raiz_do_projeto)` (5 `dirname` a partir de `ciclo-4-ia-chat/server.py`).

## Próximo

Corrigir timeout da busca MCP (-32603) para destravar RAG (bloco H, parte 2) e decidir o próximo ciclo web (uvicorn puro, mais rotas, persistência de conversa).
