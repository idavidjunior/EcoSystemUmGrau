---
tags: [bug, every, mp3player-metadata-rescue, reset, restart, switch]
aliases: [**EQ state not persisted**]
date: 2026-08-20
---

# **EQ state not persisted**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
EQ enabled/disabled state not saved to SharedPreferences — switch reset to ON on every restart.

## Correcao
Added `KEY_ENABLED` to `saveActivePreset()`/`loadActivePreset()`. Uses `restoringEqState` flag to prevent listener firing during restoration.
## Conexoes

- [[bug-hub-bugs]]
- [[calls-searchonlinesearchmoderelaxed-uses-relaxed-thresholds-]]
- [[cluster-hub-mp3player]]
- [[if-relaxed-also-fails-user-sees-tente-editar-manualmente-os-]]
- [[step-0-acoustid-fingerprint-acoustidservicesearchbyfile-almo]]
- [[user-taps-buscar-na-internet]]