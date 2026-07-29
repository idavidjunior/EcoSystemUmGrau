---
tags: [bug, mp3player-metadata-rescue]
aliases: [**Audio stops / EQ not audible**]
date: 2026-07-29
---

# Bug: **Audio stops / EQ not audible**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
`EqualizerAudioProcessor.queueInput()` never calls `inputBuffer.position(inputBuffer.limit())` after processing. ExoPlayer sees 0 bytes consumed → audio pipeline stalls. Also `isActive()` was initiall

## Correcao
1. Call `inputBuffer.position(inputBuffer.limit())` after successful processing. 2. Make `isActive()` always return `true`; use internal `isActiveState` flag to decide bypass vs processing inside `que
