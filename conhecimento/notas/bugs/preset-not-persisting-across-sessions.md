---
tags: [audible, bug, mp3player-metadata-rescue, never, projeto, separate]
aliases: [**Preset not persisting across sessions**]
date: 2026-08-20
---

# **Preset not persisting across sessions**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
The preamp was baked into `currentGains[]` making it irreversible. `syncSoftwareEq()` passed preamp=0 to processor so preamp was never audible.

## Correcao
**Refactored:** `currentGains[]` now stores RAW gains only, `currentPreamp` is separate. `applyPreset()` no longer bakes preamp into gains. `syncSoftwareEq()` passes `currentPreamp` to processor. Adde
## Conexoes

- [[bug-hub-bugs]]
- [[calls-searchonlinesearchmoderelaxed-uses-relaxed-thresholds-]]
- [[cluster-hub-mp3player]]
- [[if-relaxed-also-fails-user-sees-tente-editar-manualmente-os-]]
- [[step-0-acoustid-fingerprint-acoustidservicesearchbyfile-almo]]
- [[user-taps-buscar-na-internet]]