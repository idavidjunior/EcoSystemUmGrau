---
tags: [bug, mp3player-metadata-rescue]
aliases: [**EQ only applies after opening fragment**]
date: 2026-08-01
---

# Bug: **EQ only applies after opening fragment**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
Saved gains/preamp never loaded into processor until `EqualizerFragment.loadActivePreset()` runs. Playing a song without opening EQ meant processor stayed flat.

## Correcao
Added `EqStateLoader.restoreTo()` — loads same SharedPreferences used by fragment and applies to processor. Called in `playSongFromList()` before playing.
