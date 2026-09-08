# GAP ANALYSIS — Engenharia Web

**Categoria:** padrao
**Fonte:** Auditoria de ambiente e acervo (2026-09-08)
**Projeto:** EcoSystemUmGrau
**Dominio:** Engenharia Web

## Problema

O ecossistema quer possuir engenharia web como capacidade operacional permanente, mas ainda não mediu o que já tem vs. o que falta. Este documento é o mapa objetivo de lacunas por bloco de competência (A–L), com pistas de o que fazer para cada uma.

## Método

Auditoria de ambiente real (imports / instalações verificados um a um) + auditoria de acervo (skills MCP, vault, projetos no repo). Sem adivinhação: só o que foi visto e testado entra como evidência.

## Lacunas por bloco

### A Fundamentos (HTML/CSS/HTTP/JSON/DOM)
Já tem: www/ estático (index, eco-vox, cerebro, terminal_widget.css), skills MCP de fundamentos.
Falta: labs executados e validados; padronização em conhecimento/web.
Ação: micro-labs ciclo 1 — servidor HTTP stdlib, HTML semântico, JSON, DOM.

### B Frontend React/Next/PWA
Já tem: Projetos/Rob-Trader (React 19 + Vite 7 + TS 5.9 + Express 5) — código real mas sem runtime.
Falta: Node.js/npm (decisão externa), execução validada.
Ação: esperar decisão de instalar Node ou manter PWA/vanilla por ora.

### C TypeScript
Já tem: padrões TS no vault.
Falta: runtime Node para compilar/testar.
Ação: mesmo bloqueio do B.

### D UI/UX
Já tem: exemplos (EcoDashboard, WindowGUI, www/), skill accessibility.
Falta: avaliação WCAG real, design system próprio.
Ação: micro-lab de acessibilidade + manutenção do padrão dark existente.

### E Animação/Gráficos WebGL/Three.js/WebGPU
Já tem: docs/grafo.html, docs/grafo_widget.html, skill graphify.
Falta: validar se funcionam; WebGPU não testado.
Ação: rodar/acessar os grafos existentes e registrar evidência.

### F Backend Web
Já tem: stdlib http.server, uvicorn, httpx, requests, websockets, aiohttp, playwright, jinja2 3.1.6, pydantic 2.13.4.
Falta: escolha/ADR de framework (FastAPI/Flask não instalados), testes de integração.
Ação: partir de stdlib+uvicorn; ADR de framework quando o ciclo 2 exigir; instalar FastAPI só com justificativa.

### G Banco (PostgreSQL/Redis)
Já tem: sqlite3 (stdlib) comprovado.
Falta: verificação de PostgreSQL/Redis no ambiente; decisão se o produto exigir.
Ação: manter sqlite3 para estado local; expandir só se a demanda real surgir.

### H IA/LLM/RAG em web
Já tem: cognitive_core (sys.path fix validado), agents amarrados aos loops, MCP de conhecimento/skills — VALIDATED no núcleo.
Falta: expor essa IA como interface web (chat, dashboard), RAG com busca MCP (que está com timeout -32603).
Ação: ciclo de IA — montar endpoint web que conversa com o núcleo; corrigir timeout da busca MCP antes de RAG.

### I Segurança OWASP
Já tem: skills secure-coding, threat-modeling, security-review, compliance-audit.
Falta: aplicar checklist em um produto web real (laboratório).
Ação: cada micro-lab registra secção de segurança no template; ciclo de segurança revisa o conjunto.

### J Performance / Core Web Vitals
Já tem: skill performance-testing, playwright instalado.
Falta: medições reais (LCP/CLS/INP) em qualquer página do repo.
Ação: micro-lab de medição com playwright nas páginas www/.

### K DevOps
Já tem: gate persistencia.ps1, GitHub Actions usados (build Android/Flutter), skill ci-cd-pipeline.
Falta: Docker no ambiente; pipeline para produto web próprio.
Ação: manter CI via GitHub Actions; Docker só quando produto web exigir.

### L Arquitetura
Já tem: ADRs anteriores já consolidados pelo ecossistema (Raspberry/Android/Linux/watcher, método 3 camadas web).
Falta: ADRs específicos das decisões web deste plano (stack, padrão de camadas).
Ação: registrar ADR-001..010 à medida que decisões forem tomadas (formato template-decisao).

## Resumo executivo

- Há uma base real e instalada para começar: Python stdlib + uvicorn + aiohttp + websockets + playwright + jinja2 + sqlite3.
- Dois bloqueios de decisão externa: Node.js/npm (B, C) e PostgreSQL/Redis (G). Nenhum impede o início.
- Dois pontos frágeis do ecossistema: timeout da busca MCP (H) e hang do memory_engine (registro). Tratar antes de RAG e antes de qualquer lab que dependa de memória.
- A maioria dos blocos está em DISCOVERED/UNDERSTOOD com nível 1–3: o caminho é execução validada (labs), não mais auditoria.

## Quando usar

Consultar antes de iniciar qualquer ciclo, ao responder "o que falta para web", e ao priorizar trabalho no produto web.