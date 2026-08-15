---
tags: [bug, bypass, inside, mp3player-metadata-rescue, pipeline, stalls]
aliases: [**Audio stops / EQ not audible**]
date: 2026-08-15
---

# **Audio stops / EQ not audible**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
`EqualizerAudioProcessor.queueInput()` never calls `inputBuffer.position(inputBuffer.limit())` after processing. ExoPlayer sees 0 bytes consumed → audio pipeline stalls. Also `isActive()` was initiall

## Correcao
1. Call `inputBuffer.position(inputBuffer.limit())` after successful processing. 2. Make `isActive()` always return `true`; use internal `isActiveState` flag to decide bypass vs processing inside `que
## Conexoes

- [[bug-hub-bugs]]
- [[calls-searchonlinesearchmoderelaxed-uses-relaxed-thresholds-]]
- [[cluster-hub-mp3player]]
- [[if-relaxed-also-fails-user-sees-tente-editar-manualmente-os-]]
- [[step-0-acoustid-fingerprint-acoustidservicesearchbyfile-almo]]
- [[user-taps-buscar-na-internet]]