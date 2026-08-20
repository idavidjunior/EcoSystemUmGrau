---
tags: [bug, frequency, increment, mp3player-metadata-rescue, playsongfromlist, sortmode]
aliases: [**No most-played tracking**]
date: 2026-08-20
---

# **No most-played tracking**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
App had no mechanism to count or sort by play frequency.

## Correcao
Added `PlayCountManager` (JSON in SharedPreferences), increment on `playSongFromList()`, `SortMode.PLAY_COUNT` in `SongAdapter.sortSongs()`, "Mais Tocadas" option in sort dialog.
## Conexoes

- [[bug-hub-bugs]]
- [[calls-searchonlinesearchmoderelaxed-uses-relaxed-thresholds-]]
- [[cluster-hub-mp3player]]
- [[if-relaxed-also-fails-user-sees-tente-editar-manualmente-os-]]
- [[step-0-acoustid-fingerprint-acoustidservicesearchbyfile-almo]]
- [[user-taps-buscar-na-internet]]