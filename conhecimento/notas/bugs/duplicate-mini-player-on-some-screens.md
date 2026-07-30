---
tags: [bug, mp3player-metadata-rescue]
aliases: [**Duplicate mini-player on some screens**]
date: 2026-07-30
---

# Bug: **Duplicate mini-player on some screens**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
`openNowPlaying()` could be called multiple times, adding duplicate fragments.

## Correcao
Added guard at start of `openNowPlaying()`: if backstack top is already "now_playing", return early.
