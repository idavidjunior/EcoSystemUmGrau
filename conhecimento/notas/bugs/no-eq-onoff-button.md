---
tags: [bug, default, fragment, header, mp3player-metadata-rescue, widget]
aliases: [**No EQ on/off button**]
date: 2026-08-02
---

# **No EQ on/off button**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
User had no way to bypass EQ without resetting all gains to zero.

## Correcao
Added `enabled` flag in `EqualizerAudioProcessor`, `setEnabled()` method, `Switch` widget in fragment header (default ON). Toggle disables both HW and SW EQ.
## Conexoes

- [[bug-hub-bugs]]
- [[calls-searchonlinesearchmoderelaxed-uses-relaxed-thresholds-]]
- [[cluster-hub-mp3player]]
- [[if-relaxed-also-fails-user-sees-tente-editar-manualmente-os-]]
- [[step-0-acoustid-fingerprint-acoustidservicesearchbyfile-almo]]
- [[user-taps-buscar-na-internet]]