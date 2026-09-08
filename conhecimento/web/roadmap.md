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

### Ciclo 2 — Backend estruturado (F/L)
Micro-labs: rotas múltiplas, parâmetros, status codes corretos, eros JSON (404/405/500), servidores concorrentes (ThreadingHTTPServer vs uvicorn). ADR-003 (stack web core): decisão entre uvicorn puro vs FastAPI. Entrega: mini-API com 3+ rotas + teste de integração.

### Ciclo 3 — Realtime WebSocket (F/H)
Micro-labs: WebSocket com aiohttp/websockets; broadcast; heartbeat. Integração com o runtime persistente (estado eco). Entrega: endpoint WS eco validado com cliente de teste.

### Ciclo 4 — IA como interface web (H/A)
Micro-labs: endpoint POST que conversa com cognitive_core/agents; chat simples; JS do lado cliente consumindo fetch. PRÉ-REQUISITO: corrigir timeout da busca MCP (-32603) antes de RAG. Entrega: chat web básico ligado a um agente real.

### Ciclo 5 — Persistência web (G)
Micro-labs: sqlite3 em servidor HTTP; tabelas, queries, migrations simples; ponto único de persistência (gate). Entrega: app web que persiste estado local real.

### Ciclo 6 — Segurança OWASP (I)
Micro-labs: validação de entrada, headers seguros, CORS, sanitização, rate limit. Auditoria com skill security-review nos labs anteriores. Entrega: checklist de segurança aplicado ao conjunto.

### Ciclo 7 — Performance e acessibilidade (J/D)
Micro-labs: medição de LCP/CLS/INP com playwright; correção de acesso (WCAG básico). Entrega: relatório de Core Web Vitals de uma página real + correções.

### Ciclo 8 — Produto web integrado (projeto N1–N5)
Construção de um micro-produto web real que usa: servidor, API, WS, sqlite, IA, segurança e performance. Critério de conclusão: 20 demonstrações (conforme missão). Entrega: produto + 20 evidências no mapa.

### Ciclo 9 — Padronização e publicação (K)
Micro-labs: build/run script reproduzível, documentação de operação, deploy via GitHub Pages ou pipe existente. Entrega: runbook de operação web.

## Decisões externas pendentes (não bloqueiam o início)

- Node.js/npm (blocos B/C): perguntar ao usuário. Alternativa até lá: manter stack Python/PWA; quando decidido, usar acervo Rob-Trader como base.
- PostgreSQL/Redis (bloco G): só se o produto exigir.
- Docker (bloco K): só se necessário.

## Regras do roadmap

1. Ciclos não pulem: os de dependência vêm primeiro.
2. Cada ciclo termina com teste executado e evidência em labs/.
3. Decisões arquiteturais → ADR (template-decisao).
4. Bugs de infra (timeout MCP, memory_engine hang) entram como falhas/ e bloqueiam só o ciclo que depender deles.
5. Revisar o roadmap ao fim de cada ciclo; nunca executar 2 ciclos de uma vez.

## Quando usar

Referência de sequenciamento de toda a capacitação web. Consultar ao iniciar cada ciclo e ao priorizar tarefas.