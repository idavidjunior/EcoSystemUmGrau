---
tags: [bug, mp3player-metadata-rescue]
aliases: [**Preset data corrupted on pt_BR locale**]
date: 2026-07-29
---

# Bug: **Preset data corrupted on pt_BR locale**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
`"%.1f".format(-4.0)` produces `"-4,0"` (comma decimal) on Brazilian locale. `joinToString(",")` uses same comma → data splits into 2x the expected parts.

## Correcao
Changed separator to `
