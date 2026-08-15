---
tags: [cognitivo, cortado, general, grandes, relatórios, tinham]
aliases: [fix tts corte final textos longos]
date: 2026-08-15
---

# fix tts corte final textos longos

**Dominio:** general

---
tipo: erro
tags: [tts, speech_pipeline, chunking, truncamento, edge-tts]
data: 2026-08-13
contexto: Textos longos narrados por voz (resumos grandes, relatórios) tinham o final cortado
decisao: O SpeechPipeline.prepare() truncava o texto em MAX_TEXT_LENGTH (2000) antes da síntese,
cortando silenciosamente todo o conteúdo restante. Corrigido movendo o split de texto longo
para a síntese: _partes_para_sintese() divide via SentenceChunker.chunk_by_length() e a
síntese concatena o áudio de cada p
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]