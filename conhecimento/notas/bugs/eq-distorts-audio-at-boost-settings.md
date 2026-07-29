---
tags: [bug, mp3player-metadata-rescue]
aliases: [**EQ distorts audio at boost settings**]
date: 2026-07-29
---

# Bug: **EQ distorts audio at boost settings**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
20 cascaded peaking filters + preamp can push signal past 1.0. `coerceIn(-1f, 1f)` causes hard clipping distortion.

## Correcao
Replaced `coerceIn(-1f, 1f)` with `Math.tanh(sample)` — soft-clipping (tube-like saturation). Also made `isActive()` always return `true` to prevent ExoPlayer from caching the inactive state.
