---
tags: [decisao, machine, opencode, state, tdd, workflow]
aliases: [Reorganização: Habilidades dentro de MCP por domínio]
date: 2026-08-21
---

# Reorganização: Habilidades dentro de MCP por domínio

**Fonte:** opencode

---
tipo: decisao
tags: [mcp, habilidades, reorganizacao, dominios, arquitetura]
data: 2026-08-04
contexto: Habilidades espalhadas em Habilidades/tecnicas/, pontes/ migradas para mcp/<dominio>/habilidades/ como contêineres MCP
---

# Reorganização: Habilidades dentro de MCP por domínio

## Decisão

Todas as 40 habilidades (38 técnicas + 2 pontes) movidas de Habilidades/tecnicas/ e Habilidades/pontes/ para mcp/<dominio>/habilidades/:

- desenvolvimento: 30 skills (api-design, authz-authn-matrix, backend-patterns, cache-strategy-selector, concurrent-computation-patterns, cost-aware-llm-pipeline, data-privacy-by-design, database-migrations, deployment-patterns, developer-experience-dx, docker-patterns, e2e-testing, edge-compute-patterns, error-message-design, frontend-patterns, golang-patterns, graphify, ler, local-first-architecture, migration-playbooks, multi-modal-ai, observability-stack, python-patterns, resilience-engineering, search-first, security-review, semantic-release-automation, state-machine-patterns, tdd-workflow)
- android: 4 skills (android-diagnostics, android-pure-sdk, mobile-specific-patterns, mp3player-metadata-rescue)
- internet: 4 skills (busca-web, clima-api, endereco-geo, navegacao-perita)
- memoria: 1 skill (busca-conhecimento / search_knowledge.py)

Cada domínio tem server.py (Python puro, sem npx) que expõe as habilidades como ferramentas MCP.

## Referências atualizadas

- config/opencode.jsonc + scripts/opencode-serve.jsonc: instructions globs e registro de 4 novos MCPs (mcp-desenvolvimento, mcp-android, mcp-internet, mcp-memoria)
- jarvis_bridge.py: import clima-api do mcp/internet/habilidades/clima-api
- mcp-knowledge-server.py: chama search_knowledge do mcp/memoria/habilidades/busca-conhecimento
- search_knowledge.py: BASE robusto subindo até raiz do ecossistema
- maestro (00-maestro.md), JARVIS_SYSTEM.md, test-ecosystem.ps1, AGENTS.md, 00-system-rules.md, README.md, HABILIDADES.md, estado_atual.md, MOC - Projetos.md
- manifesto_mcp.json v2.0 em mcp/manifesto_mcp.json (40 skills com dominio + path)

## Preflight

Todos testes PASS (10 MCPs testados, 3 camadas consistentes, secrets guard OK).

## Impacto

Arquitetura MCP com habilidades dentro de domínios — clone recursivo funcional, OpenCode carrega skills via instructions globs. Ecossistema limpo, sem Habilidades/tecnicas/ e pontes/ vazias removidas.

## Conexoes

- [[correcao-de-diagnostico-do-knowledge-graph-e-criacao-do-regi]]
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]