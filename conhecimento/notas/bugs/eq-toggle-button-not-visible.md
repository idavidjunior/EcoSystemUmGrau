---
tags: [active, btn, bug, mp3player-metadata-rescue, preset, styles]
aliases: [**EQ toggle button not visible**]
date: 2026-08-21
---

# **EQ toggle button not visible**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
`Switch` widget may not render correctly on some MIUI versions or was too small to notice.

## Correcao
Replaced `Switch` with `Button` styled as toggle (`EQ ON`/`EQ OFF`), matching existing button styles (`bg_preset_active`/`bg_preset_btn`). Uses `isSelected` for state.
## Conexoes

- [[bug-hub-bugs]]
- [[calls-searchonlinesearchmoderelaxed-uses-relaxed-thresholds-]]
- [[cluster-hub-mp3player]]
- [[if-relaxed-also-fails-user-sees-tente-editar-manualmente-os-]]
- [[step-0-acoustid-fingerprint-acoustidservicesearchbyfile-almo]]
- [[user-taps-buscar-na-internet]]