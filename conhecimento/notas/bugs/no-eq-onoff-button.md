---
tags: [bug, mp3player-metadata-rescue]
aliases: [**No EQ on/off button**]
date: 2026-07-30
---

# Bug: **No EQ on/off button**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
User had no way to bypass EQ without resetting all gains to zero.

## Correcao
Added `enabled` flag in `EqualizerAudioProcessor`, `setEnabled()` method, `Switch` widget in fragment header (default ON). Toggle disables both HW and SW EQ.
