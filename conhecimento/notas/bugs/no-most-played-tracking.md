---
tags: [bug, mp3player-metadata-rescue]
aliases: [**No most-played tracking**]
date: 2026-07-29
---

# Bug: **No most-played tracking**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
App had no mechanism to count or sort by play frequency.

## Correcao
Added `PlayCountManager` (JSON in SharedPreferences), increment on `playSongFromList()`, `SortMode.PLAY_COUNT` in `SongAdapter.sortSongs()`, "Mais Tocadas" option in sort dialog.
