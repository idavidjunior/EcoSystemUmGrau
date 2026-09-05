---
tags: [assessments, decisao, funciona, opencode, persiste, quebrar]
aliases: [auto evolution e behavior slices]
date: 2026-08-28
---

# auto evolution e behavior slices

**Fonte:** opencode

## Decisão

Criar dois módulos novos inspirados no Cartographer e aprimorar a infraestrutura existente de forma aditiva (sem quebrar o que funciona).

## O que foi feito

1. **scripts/auto_evolution.py** — Motor de auto-análise: compara capacidades de referências externas (ex: Cartographer) com as do ecossistema, detecta gaps, gera planos de evolução com steps/validação/rollback, e persiste assessments. Comandos: `scan`, `gaps`, `plan`, `assess`, `evolve`, `status`.

2. **scripts/behavior_slices.py** — Rastreio de fluxos de comportamento (flows) e changesets, com evidence-grounding (SourceAnchor, ConfidenceLevel, ProvenanceKind). Integra com memory_engine para busca semântica.

3. **scripts/memory_engine.py** — Adicionado parâmetro `source_anchors` (aditivo, não quebra nada) para evidence-grounding de memórias.

4. **scripts/runtime_state.py** — Adicionado backup pré-restore automático no `restore()`.

5. **config/opencode.jsonc** — Adicionado comando `/autoevolve`.

## Aprendizado crí
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]