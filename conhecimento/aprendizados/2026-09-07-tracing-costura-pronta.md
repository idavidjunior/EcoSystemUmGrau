---
tipo: episodio
tags: [tracing, costura, evolucao, pronto-quando-precisar]
data: 2026-09-07
contexto: deixar ecossistema pronto para tracing sem implementar tudo agora
decisao: costura eco_trace desligada por padrão com API estável e teste isolado
impacto: evolução futura pluga coletor sem mexer nos chamadores nem no comportamento
---

A API tem trace e span e finalizar desde já.
Desligada ela retorna ids sem gravar nada nem gastar tempo.
Ligada ela grava rascunho local com redação de segredo.
O teste provou silêncio padrão e gravação com teto.
A spec completa segue proposta para a hora da escala.
