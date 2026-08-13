---
tipo: erro
tags: [tts, speech_pipeline, chunking, truncamento, edge-tts]
data: 2026-08-13
contexto: Textos longos narrados por voz (resumos grandes, relatórios) tinham o final cortado
decisao: O SpeechPipeline.prepare() truncava o texto em MAX_TEXT_LENGTH (2000) antes da síntese,
cortando silenciosamente todo o conteúdo restante. Corrigido movendo o split de texto longo
para a síntese: _partes_para_sintese() divide via SentenceChunker.chunk_by_length() e a
síntese concatena o áudio de cada parte. O prepare() agora preserva o texto completo, e o
TTSValidator passou a lançar TextTooLongError para texto acima do limite (sem truncar).
impacto: Áudio de texto longo cresce proporcionalmente ao texto (validado: 2032 chars -> 1.7MB;
5272 chars -> 4.9MB; razão bytes 2.83 para razão chars 2.59). Nenhum final de fala é mais cortado.
Validador, cache e streaming seguem funcionando (test_cache.py, test_acento.py, stream() com
4347 chunks OK). Memory #267 registrada.
erros_encontrados:
  - truncamento silencioso em prepare() cortava o final da fala
  - import não utilizado de MAX_TEXT_LENGTH em text_normalizer.py (removido)
