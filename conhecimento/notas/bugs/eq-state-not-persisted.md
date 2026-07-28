---
tags: [bug, mp3player-metadata-rescue]
aliases: [**EQ state not persisted**]
date: 2026-07-28
---

# Bug: **EQ state not persisted**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
EQ enabled/disabled state not saved to SharedPreferences — switch reset to ON on every restart.

## Correcao
Added `KEY_ENABLED` to `saveActivePreset()`/`loadActivePreset()`. Uses `restoringEqState` flag to prevent listener firing during restoration.
