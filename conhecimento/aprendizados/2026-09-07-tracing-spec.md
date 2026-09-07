---
tipo: episodio
tags: [tracing, spec, observabilidade, gargalos]
data: 2026-09-07
contexto: pedido de spec para tracing integrado antes de escalar
decisao: spec proposta em specs/eco-tracing.spec.md com coletor local e exportação opcional
impacto: base pronta para implementar scripts/eco_trace.py com spans nos pontos quentes
---

Nenhum tracing externo existe hoje no ecossistema.
O roteador e o orchestrator têm pontos naturais de span.
O requests já é dependência homologada para exportar.
A spec prevê local primeiro com backend como espelho.
Ela exige erro sempre gravado e falha externa sem quebrar.
