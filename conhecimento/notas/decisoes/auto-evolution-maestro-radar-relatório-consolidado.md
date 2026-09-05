---
tags: [aprendizados, conhecimento, decisao, opencode, orquestram, yyyy]
aliases: [Auto-Evolution: Maestro + Radar + Relatório Consolidado]
date: 2026-09-03
---

# Auto-Evolution: Maestro + Radar + Relatório Consolidado

**Fonte:** opencode

Fecha os 3 itens pendentes do motor de auto-evolução do Ecossistema.

## Decisões

1. Maestro: nova funcao `_maestro_consulta` usa `maestro_client.consultar_maestro` antes de delegar cada plano em `_execute_plan`. Fail-soft: se offline, evolucao segue sem travar. Status 'blocked' do Maestro bloqueia o plano.
2. Busca externa: novo subcomando `radar` e funcao `_collect_external_gaps` orquestram `evolution_radar_collect.py --full` (collect->filter->package). Reutiliza coletor existente, nao duplica. Exige flag `EVOLUTION_RADAR_ADMIN=1` (confirmacao de admin antes de buscar na internet).
3. Relatorio consolidado: funcao `_save_cycle_learning_report` gera `conhecimento/aprendizados/YYYY-MM-DD-auto-evolucao.md` ao final de cada ciclo apply, alem do JSON interno em runtime/learning/evolution.

## Bug corrigido (detecção automática)

`evolution_radar_collect.py` falhava em `save_state` com `TypeError: Object of type set is not JSON serializable` ao coletar itens novos. Causa: `seen_hashes[src
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]