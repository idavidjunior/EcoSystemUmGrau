---
tags: [bug, master, mp3player-metadata-rescue, multiplier, never, sent]
aliases: [**Preamp not audible**]
date: 2026-08-13
---

# **Preamp not audible**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
`syncSoftwareEq()` always called `mp.setEqPreampGain(0f)`, ignoring `currentPreamp`. The preamp was only baked into HW EQ gains, never sent to software EQ.

## Correcao
`syncSoftwareEq()` now calls `mp.setEqPreampGain(currentPreamp)` instead of `0f`. Software EQ receives preamp as a master multiplier.
## Conexoes

- [[bug-hub-bugs]]
- [[calls-searchonlinesearchmoderelaxed-uses-relaxed-thresholds-]]
- [[cluster-hub-mp3player]]
- [[if-relaxed-also-fails-user-sees-tente-editar-manualmente-os-]]
- [[step-0-acoustid-fingerprint-acoustidservicesearchbyfile-almo]]
- [[user-taps-buscar-na-internet]]