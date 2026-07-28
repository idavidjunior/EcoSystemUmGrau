---
tags: [bug, mp3player-metadata-rescue]
aliases: [**EQ still distorts at high boost**]
date: 2026-07-27
---

# Bug: **EQ still distorts at high boost**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
`tanh()` soft-clipping alone insufficient — 20 cascaded peaking filters + preamp can produce cumulative gain >> 6 dB at certain frequencies, exceeding `tanh()` saturation threshold.

## Correcao
Added peak limiter in `queueInput()`: measure peak after filter cascade, apply gain reduction (1.0/peak) with per-sample attack/release smoothing (1ms attack, 100ms release). `tanh()` remains as final
