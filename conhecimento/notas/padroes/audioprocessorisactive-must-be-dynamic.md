---
tags: [padrao, mp3player]
aliases: [AudioProcessor.isActive() must be dynamic]
date: 2026-07-30
---

# AudioProcessor.isActive() must be dynamic

**Fonte:** mp3player

isActive() retorna true apenas quando preampGainDb != 0 || any band gain != 0. queueInput() DEVE chamar inputBuffer.position(inputBuffer.limit()) apos processar. Se nao, ExoPlayer ve 0 bytes consumidos e o audio trava.
