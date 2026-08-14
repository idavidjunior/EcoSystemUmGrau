---
tags: [bug, caching, exoplayer, inactive, mp3player-metadata-rescue, state]
aliases: [**EQ distorts audio at boost settings**]
date: 2026-08-14
---

# **EQ distorts audio at boost settings**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
20 cascaded peaking filters + preamp can push signal past 1.0. `coerceIn(-1f, 1f)` causes hard clipping distortion.

## Correcao
Replaced `coerceIn(-1f, 1f)` with `Math.tanh(sample)` — soft-clipping (tube-like saturation). Also made `isActive()` always return `true` to prevent ExoPlayer from caching the inactive state.
## Conexoes

- [[bug-hub-bugs]]
- [[calls-searchonlinesearchmoderelaxed-uses-relaxed-thresholds-]]
- [[cluster-hub-mp3player]]
- [[if-relaxed-also-fails-user-sees-tente-editar-manualmente-os-]]
- [[step-0-acoustid-fingerprint-acoustidservicesearchbyfile-almo]]
- [[user-taps-buscar-na-internet]]