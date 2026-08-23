---
tags: [criterios, decisao, estritamente, evidencias, opencode, separados]
aliases: [pais]
date: 2026-08-23
---

# pais

**Fonte:** opencode

---
tipo: decisao
tags: [pais, adaptativo, integridade-epistemica, nucleo]
data: 2026-08-14
contexto: Implementacao do PAIS (Personal Adaptive Intelligence System) no nucleo do ecossistema, com 21 modulos de aprendizado adaptativo do usuario.
decisao: Criar habilidade em mcp/nucleo/habilidades/pais com user model e epistemic model estritamente separados (storage/user_model.json vs storage/epistemic_model.json). Codigo heuristico determinístico em Python stdlib, sem LLM, fail-soft. Guardas anti-bajulacao e anti-alucinacao no pipeline de resposta. CLI em cli.py (rename por colisao de nome com o pacote pais/).
impacto: Todo agente pode personalizar a forma das respostas (profundidade, estrutura, exemplos, tom) sem nunca alterar fatos, evidencias ou criterios de validacao. Auditoria via report com metricas separadas.
regra-de-ouro: PERSONALIZE A INTERACAO. NAO PERSONALIZE A VERDADE. Prioridade: VERDADE > EVIDENCIA > RAZAO > TRANSPARENCIA > UTILIDADE > PERSONALIZACAO.
validacao: 18 testes (secao 29 do pedido) passando + preflight_check.py TODOS TESTES PASSARAM.
bugs-corrigidos: classify de evidencia avaliada em ordem errada (conflito antes de qualidade); topic_frequency sem most_common; limiar de phrase de incerteza; deteccao de "sem evidencia" no review; regex de anti-alucinacao sem "testei/passou"; atributo self.feedback sobrescrevia metodo.

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]