# ROADMAP — Aquisição de Engenharia Web

**Categoria:** padrao
**Fonte:** Missão permanente de capacitação web (2026-09-08)
**Projeto:** EcoSystemUmGrau
**Dominio:** Engenharia Web

## Problema

Transformar "saber sobre web" em "possuir engenharia web operacional": base documentada, labs validados, decisões registradas em ADR, e evidência de integração com o resto do ecossistema.

## Solução

Trilha em ciclos curtos, cada um com entrega validada (teste real) e registro em conhecimento/web. Norteador: APRENDA → EXPERIMENTE → TESTE → VALIDE → CONSOLIDE → INTEGRE → PADRONIZE → OBSERVE → EVOLUA. Stack inicial Jedi: Python stdlib + uvicorn + aiohttp + websockets + playwright + jinja2 + sqlite3. Não esperar Node/PostgreSQL para começar.

## Ciclos

### Ciclo 1 — Fundamentos (A/F) — concluído (2026-09-08)
Micro-labs: servidor HTTP stdlib, HTML semântico + CSS dark, JSON, DOM. Entrega: página servida por http.server com /api/health, validada por teste httpx real em labs/ciclo-1-fundamentos (test_server.py PASSANDO; mapa bloco A = VALIDATED/3).

### Ciclo 2 — Backend estruturado (F/L) — concluído (2026-09-08)
Mini-API Python stdlib com rotas múltiplas (/api/health, /api/soma, /api/items, /api/explode), parâmetros via query string, status codes corretos (200/201/400/404/405/500) e erros JSON, validada por teste de integração em labs/ciclo-2-backend-estruturado (STATUS OK, 14 checks, 0 falhas; adversarial incluído). ADR-003 decidiu: manter/estender ThreadingHTTPServer stdlib; uvicorn puro documentado para Ciclos 4+; FastAPI fora.

### Ciclo 3 — Realtime WebSocket (F/H) — concluído (2026-09-08)
Servidor WebSocket (websockets 17, asyncio) com eco, broadcast, heartbeat e integração com o estado persistente do runtime (rota /estado), validado por cliente de teste real em labs/ciclo-3-websocket (STATUS OK, 6 checks, 0 falhas). ADR-004 decidiu: websockets 17 como camada WS; aiohttp como alternativa de HTTP+WS; uvicorn puro adiado para Ciclos 4+.

### Ciclo 4 — IA como interface web (H/A) — concluído (2026-09-09)
Endpoint POST que conversa com o cognitive_core real (`process_user_input`), chat HTML/JS consumindo fetch, validado por teste de integração em labs/ciclo-4-ia-chat (STATUS OK, 11 checks, 0 falhas). ADR-003 mantido (stdlib HTTP). RAG pendente de implementação — timeout de busca MCP (-32603) corrigido em 09/09 (timeouts realinhados e lock concorrente de memória com espera 120s; add-memory validado, memória 98318).

### Ciclo 5 — Persistência web (G) — concluído (2026-09-09)
Micro-labs: sqlite3 em servidor HTTP; tabelas, queries, migrations simples; ponto único de persistência (gate). Entrega: app web que persiste estado local real. Validado em labs/ciclo-5-persistencia-web (STATUS OK, 25 checks, 0 falhas; CRUD + arquivar + excluir + persistência real entre reinícios). ADR-005 decidiu: sqlite3 stdlib como camada de banco (bloco G VALIDATED/3); ThreadingHTTPServer mantido (ADR-003); PostgreSQL/Redis só se o produto exigir.

### Ciclo 6 — Segurança OWASP (I) — concluído (2026-09-09)
SecurityMiddleware com headers OWASP (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, CSP), rate limit token bucket (50/min por IP), limite de body (1MB), validação de Content-Type (JSON only), sanitização de strings, tratamento de erros sem leak de internals, SQL injection blocking, endpoint /api/explode para teste de erro 500. Validado em labs/ciclo-6-seguranca-owasp (STATUS OK, 34 checks, 0 falhas). ADR-006 decidiu: middleware OWASP próprio em stdlib (mixin reutilizável).

### Ciclo 7 — Performance e acessibilidade (J/D) — concluído (2026-09-09)
Micro-labs: medição de LCP/CLS/INP com Playwright; correção de acesso (WCAG básico). Entrega validada em labs/ciclo-7-performance-acessibilidade (STATUS OK, 18 checks, 0 falhas; CWV de página real antes/depois + a11y). ADR-007 decidiu: Playwright sync + PerformanceObserver para medir CWV; atraso artificial no asset permite medir em loopback.

### Ciclo 8 — Produto web integrado (projeto N1–N5)
Construção de um micro-produto web real que usa: servidor, API, WS, sqlite, IA, segurança e performance. Critério de conclusão: 20 demonstrações (conforme missão). Entrega: produto + 20 evidências no mapa.

### Ciclo 9 — Padronização e publicação (K)
Micro-labs: build/run script reproduzível, documentação de operação, deploy via GitHub Pages ou pipe existente. Entrega: runbook de operação web.

## Decisões externas pendentes (não bloqueiam o início)

- Node.js/npm (blocos B/C): perguntar ao usuário. Alternativa até lá: manter stack Python/PWA; quando decidido, usar acervo Rob-Trader como base.
- PostgreSQL/Redis (bloco G): só se o produto exigir.
- Docker (bloco K): só se necessário.
- Lighthouse/npx: ADR-007 decidiu Playwright + PerformanceObserver; Lighthouse fica fora por depender de Node ausente.

## Regras do roadmap

1. Ciclos não pulem: os de dependência vêm primeiro.
2. Cada ciclo termina com teste executado e evidência em labs/.
3. Decisões arquiteturais → ADR (template-decisao).
4. Bugs de infra (timeout MCP, memory_engine hang) entram como falhas/ e bloqueiam só o ciclo que depender deles.
5. Revisar o roadmap ao fim de cada ciclo; nunca executar 2 ciclos de uma vez.

## Quando usar

Referência de sequenciamento de toda a capacitação web. Consultar ao iniciar cada ciclo e ao priorizar tarefas.