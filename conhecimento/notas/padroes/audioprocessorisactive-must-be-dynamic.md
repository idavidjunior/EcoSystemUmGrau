---
tags: [audio, bytes, consumidos, mp3player, padrao, trava]
aliases: [AudioProcessor.isActive() must be dynamic]
date: 2026-08-14
---

# AudioProcessor.isActive() must be dynamic

**Fonte:** mp3player

isActive() retorna true apenas quando preampGainDb != 0 || any band gain != 0. queueInput() DEVE chamar inputBuffer.position(inputBuffer.limit()) apos processar. Se nao, ExoPlayer ve 0 bytes consumidos e o audio trava.
## Conexoes

- [[cluster-hub-mp3player]]
- [[filename-artist-extraction-two-strategies]]
- [[itunes-search-with-scoring-thresholds]]
- [[metadata-busca-em-multi-fontes-acoustid-itunes-br-musicbrain]]
- [[padrao-hub-padroes]]
- [[renderersfactory-for-custom-audioprocessor]]