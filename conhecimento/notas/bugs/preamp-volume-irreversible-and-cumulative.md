---
tags: [bug, mp3player-metadata-rescue]
aliases: [**Preamp volume irreversible and cumulative**]
date: 2026-07-28
---

# Bug: **Preamp volume irreversible and cumulative**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
`showVolumeDialog()` did `currentGains[i] += v` on already-baked gains. Each call added more, preamp could never be undone without reset.

## Correcao
Fixed by the same refactoring: preamp is now separate. `showVolumeDialog()` only updates `currentPreamp` and re-applies HW EQ bands without touching `currentGains[]`.
