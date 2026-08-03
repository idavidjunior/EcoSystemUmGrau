---
tags: [actual, always, bug, enabled, gains, mp3player-metadata-rescue]
aliases: [**EQ deactivates on song change**]
date: 2026-08-02
---

# **EQ deactivates on song change**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
`AudioProcessor.reset()` set `isActiveState = false` and `configure()` never recalculated it. ExoPlayer calls `reset()` between songs → processor silently bypassed.

## Correcao
Added `updateActiveState()` call in `configure()` and `reset()`. Removed `isActiveState = false` from `reset()` — state is now always recalculated from actual gains/enabled.
## Conexoes

- [[bug-hub-bugs]]
- [[calls-searchonlinesearchmoderelaxed-uses-relaxed-thresholds-]]
- [[cluster-hub-mp3player]]
- [[if-relaxed-also-fails-user-sees-tente-editar-manualmente-os-]]
- [[step-0-acoustid-fingerprint-acoustidservicesearchbyfile-almo]]
- [[user-taps-buscar-na-internet]]