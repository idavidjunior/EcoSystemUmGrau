---
tags: [bug, equalizerfragment, flat, mp3player-metadata-rescue, stayed, until]
aliases: [**EQ only applies after opening fragment**]
date: 2026-08-08
---

# **EQ only applies after opening fragment**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
Saved gains/preamp never loaded into processor until `EqualizerFragment.loadActivePreset()` runs. Playing a song without opening EQ meant processor stayed flat.

## Correcao
Added `EqStateLoader.restoreTo()` — loads same SharedPreferences used by fragment and applies to processor. Called in `playSongFromList()` before playing.
## Conexoes

- [[bug-hub-bugs]]
- [[calls-searchonlinesearchmoderelaxed-uses-relaxed-thresholds-]]
- [[cluster-hub-mp3player]]
- [[if-relaxed-also-fails-user-sees-tente-editar-manualmente-os-]]
- [[step-0-acoustid-fingerprint-acoustidservicesearchbyfile-almo]]
- [[user-taps-buscar-na-internet]]