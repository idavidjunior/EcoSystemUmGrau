---
tags: [bargein, decisao, inicio, opencode, responder, saudar]
aliases: [pausa total widget]
date: 2026-08-28
---

# pausa total widget

**Fonte:** opencode

Tipo: decisao

Tags: [widget, narrador, tts, voz, pausa, silenciar, dialogo]

Data: 2026-08-28

contexto: Botão "Pausar" do widget deveria silenciar todo áudio de saída, mas o estado antigo (pausado) era usado por voice_on/voice_off e só pausava a narração.

decisao: Estado mestre novo pausa_total em runtime/narracao_estado.json, separado de pausado. Todos os consumidores de áudio do PC respeitam: narrador do widget (rumo ao buffer + _flush), tts_service (speak responde ignored/pausado), dialogo (gates em tocar_base64, falar_com_bargein, responder e saudar_inicio). VAD continua escutando e Jarvis responde só em texto. voice_on/voice_off mexem só em pausado, sem tocar no mestre. Além disso, filtro _PADRAO_SUMMARY bloqueia blocos "## Objective"/resumo regravados pelo OpenCode a cada compactação de contexto (4 supressões reais validadas no log).

impacto: Silêncio total determinístico durante pausa; sem quebrar modo voz; sem redudância de estado. Mensagens durante pausa são descartadas (n
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]