---
tags: [adding, bug, early, fragments, mp3player-metadata-rescue, times]
aliases: [**Duplicate mini-player on some screens**]
date: 2026-08-15
---

# **Duplicate mini-player on some screens**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
`openNowPlaying()` could be called multiple times, adding duplicate fragments.

## Correcao
Added guard at start of `openNowPlaying()`: if backstack top is already "now_playing", return early.
## Conexoes

- [[bug-hub-bugs]]
- [[calls-searchonlinesearchmoderelaxed-uses-relaxed-thresholds-]]
- [[cluster-hub-mp3player]]
- [[if-relaxed-also-fails-user-sees-tente-editar-manualmente-os-]]
- [[step-0-acoustid-fingerprint-acoustidservicesearchbyfile-almo]]
- [[user-taps-buscar-na-internet]]