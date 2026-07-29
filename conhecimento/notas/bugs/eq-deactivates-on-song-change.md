---
tags: [bug, mp3player-metadata-rescue]
aliases: [**EQ deactivates on song change**]
date: 2026-07-29
---

# Bug: **EQ deactivates on song change**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
`AudioProcessor.reset()` set `isActiveState = false` and `configure()` never recalculated it. ExoPlayer calls `reset()` between songs → processor silently bypassed.

## Correcao
Added `updateActiveState()` call in `configure()` and `reset()`. Removed `isActiveState = false` from `reset()` — state is now always recalculated from actual gains/enabled.
