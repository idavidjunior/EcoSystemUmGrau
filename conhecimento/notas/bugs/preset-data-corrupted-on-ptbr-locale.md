---
tags: [bug, expected, mp3player-metadata-rescue, parts, projeto, splits]
aliases: [**Preset data corrupted on pt_BR locale**]
date: 2026-08-17
---

# **Preset data corrupted on pt_BR locale**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
`"%.1f".format(-4.0)` produces `"-4,0"` (comma decimal) on Brazilian locale. `joinToString(",")` uses same comma → data splits into 2x the expected parts.

## Correcao
Changed separator to `
## Conexoes

- [[bug-hub-bugs]]
- [[calls-searchonlinesearchmoderelaxed-uses-relaxed-thresholds-]]
- [[cluster-hub-mp3player]]
- [[if-relaxed-also-fails-user-sees-tente-editar-manualmente-os-]]
- [[step-0-acoustid-fingerprint-acoustidservicesearchbyfile-almo]]
- [[user-taps-buscar-na-internet]]