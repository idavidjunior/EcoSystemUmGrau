---
tags: [auditoria, contínua, decisao, medição, monitoramento, opencode]
aliases: [governanca ciclo jurisprudencia]
date: 2026-09-02
---

# governanca ciclo jurisprudencia

**Fonte:** opencode

Tipo: decisao

Tags: [governanca, jurisprudencia, clausula-petrea, evolucao-regras, decisao-arquitetural]

Data: 2026-09-02

contexto: O usuário propôs um modelo de evolução de regras do ecossistema baseado em evidência temporal: prática comprovada → jurisprudência → cláusula pétrea. O gate de persistência é o primeiro candidato a esse ciclo, tendo passado por auditoria, correção, monitoramento e medição contínua (adherence_audit.py).

decisao: Criar um ciclo de governança de três estágios para regras do ecossistema: (1) REGRA EXPERIMENTAL — regra nova, em teste, sujeita a revisão. (2) JURISPRUDÊNCIA — regra que sobreviveu a pelo menos 14 dias sem violação, com métricas monitoradas (ex.: gate_persistencia_min >= 1.0 por 14 dias consecutivos no adherence_audit) e correção automática de desvios demonstrada. Jurisprudência fica documentada em `docs/jurisprudencia.md` com data de origem, evidência e critérios de manutenção. (3) CLÁUSULA PÉTREA — regra que manteve status de jurisprudência p
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]