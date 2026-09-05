---
tags: [acontecido, decisao, knowledge, opencode, reuso, search]
aliases: [context-engine + manifesto + domínios multimídia/comportamen]
date: 2026-08-05
---

# context-engine + manifesto + domínios multimídia/comportamentais

**Fonte:** opencode

## Auditoria do estado real
- Plano listava HABILIDADES/ e scripts/ como se a reorg nao tivesse acontecido — mas ela
  ja foi feita: skills vivem em `mcp/<dominio>/habilidades/` (40 skills em 4 dominios:
  android, desenvolvimento, internet, memoria).
- Gap real: context-engine (coordenador), manifesto_geral.json, multimidia/ e
  comportamentais/ (so README, sem server.py nem skills).

## O que foi implementado
### context-engine (mcp/memoria/habilidades/context-engine/)
- `skill.md` declarativa + `context_engine.py` com 5 modos:
  - `--buscar`: BM25 unificado sobre grafo de conhecimento + memorias + notas (reuso search_knowledge.py)
  - `--paralelo`: orquestracao de subtarefas via parallel_dispatcher.py (JSON de tasks)
  - `--gravar`/`--episodio`: memoria episodica em conhecimento/episodios.json
  - `--drift`: compara estado vs SYSTEM_SPEC.md/CONHECIMENTO.md
  - `--impacto`: quem referencia um alvo (cascata)
- Exposto automaticamente pelo server MCP generico de memoria (skill-context-
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]