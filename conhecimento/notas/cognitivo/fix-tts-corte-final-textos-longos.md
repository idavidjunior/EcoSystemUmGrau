---
tags: [cognitivo, cortado, general, grandes, relatórios, tinham]
aliases: [fix tts corte final textos longos]
date: 2026-08-13
---

# fix tts corte final textos longos

**Dominio:** general

Tipo: erro

Tags: [tts, speech_pipeline, chunking, truncamento, edge-tts]

Data: 2026-08-13

contexto: Textos longos narrados por voz (resumos grandes, relatórios) tinham o final cortado

decisao: O SpeechPipeline.prepare() truncava o texto em MAX_TEXT_LENGTH (2000) antes da síntese,

impacto: Áudio de texto longo cresce proporcionalmente ao texto (validado: 2032 chars -> 1.7MB;
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]