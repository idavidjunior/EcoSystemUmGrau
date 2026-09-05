---
tags: [criterios, decisao, estritamente, opencode, separados, validacao]
aliases: [pais]
date: 2026-08-14
---

# pais

**Fonte:** opencode

Tipo: decisao

Tags: [pais, adaptativo, integridade-epistemica, nucleo]

Data: 2026-08-14

contexto: Implementacao do PAIS (Personal Adaptive Intelligence System) no nucleo do ecossistema, com 21 modulos de aprendizado adaptativo do usuario.

decisao: Criar habilidade em mcp/nucleo/habilidades/pais com user model e epistemic model estritamente separados (storage/user_model.json vs storage/epistemic_model.json). Codigo heuristico determinístico em Python stdlib, sem LLM, fail-soft. Guardas anti-bajulacao e anti-alucinacao no pipeline de resposta. CLI em cli.py (rename por colisao de nome com o pacote pais/).

impacto: Todo agente pode personalizar a forma das respostas (profundidade, estrutura, exemplos, tom) sem nunca alterar fatos, evidencias ou criterios de validacao. Auditoria via report com metricas separadas.
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]