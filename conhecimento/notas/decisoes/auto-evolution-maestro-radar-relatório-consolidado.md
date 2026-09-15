---
tags: [consistencia, decisao, load, manter, opencode, rastreabilidade]
aliases: [Auto-Evolution: Maestro + Radar + Relatório Consolidado]
date: 2026-09-03
---

# Auto-Evolution: Maestro + Radar + Relatório Consolidado

**Fonte:** opencode

---
tipo: decisao
tags: [auto-evolution, maestro, radar, evolucao, gate]
data: 2026-09-03
contexto: Fechamento dos 3 gaps pendentes do auto_evolution.py (Maestro, busca externa, relatorio consolidado).
decisao: Integrar consulta ao Maestro (fail-soft), subcomando radar com coleta externa e relatorio Markdown por ciclo.
impacto: Motor de auto-evolucao respeita governanca do Maestro, ganha busca externa real e rastreabilidade do ciclo.
---

# Auto-Evolution: Maestro + Radar + Relatório Consolidado

Fecha os 3 itens pendentes do motor de auto-evolução do Ecossistema.

## Decisões

1. Maestro: nova funcao `_maestro_consulta` usa `maestro_client.consultar_maestro` antes de delegar cada plano em `_execute_plan`. Fail-soft: se offline, evolucao segue sem travar. Status 'blocked' do Maestro bloqueia o plano.
2. Busca externa: novo subcomando `radar` e funcao `_collect_external_gaps` orquestram `evolution_radar_collect.py --full` (collect->filter->package). Reutiliza coletor existente, nao duplica. Exige flag `EVOLUTION_RADAR_ADMIN=1` (confirmacao de admin antes de buscar na internet).
3. Relatorio consolidado: funcao `_save_cycle_learning_report` gera `conhecimento/aprendizados/YYYY-MM-DD-auto-evolucao.md` ao final de cada ciclo apply, alem do JSON interno em runtime/learning/evolution.

## Bug corrigido (detecção automática)

`evolution_radar_collect.py` falhava em `save_state` com `TypeError: Object of type set is not JSON serializable` ao coletar itens novos. Causa: `seen_hashes[src]` mantido como `set()` em memoria, mas JSON nao serializa set. Corrigido com `_json_clean` (set->lista na serializacao) e conversao lista->set no `load_state` para manter consistencia em memoria.

## Validacao

- `auto_evolution.py health`: SAUDÁVEL (preflight tecnico, etico, git, memoria, checkpoint OK).
- `auto_evolution.py radar` (com admin): coleta OK, 6 candidatos, 1 pacote gerado.
- `_maestro_consulta` fail-soft: retorna offline sem bloquear.
- `preflight_check.py`: TODOS TESTES PASSARAM.

## Comandos de uso

python scripts/auto_evolution.py health   # diagnostico de saude
python scripts/auto_evolution.py radar    # busca externa de gaps (requer EVOLUTION_RADAR_ADMIN=1)

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]