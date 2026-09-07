---
tipo: episodio
tags: [agenda, spec, seguranca, idempotencia, retry]
data: 2026-09-07
contexto: pedido de spec para endurecer a agenda protótipo como infraestrutura
decisao: spec proposta em specs/eco-agenda-endurecida.spec.md com escape fechado e ciclo de disparo
impacto: base pronta para estados com retry e watchdog do tick periódico
---

O escape com ponto ponto barra foi confirmado no cálculo atual.
A idempotência cobre sobreposição mas não crash no meio da ação.
O orchestrator mostra retry com espera e o planner mostra estados.
A spec nova estende a base sem duplicar o documento anterior.
Ela prevê processo periódico com prova de vida em log.
