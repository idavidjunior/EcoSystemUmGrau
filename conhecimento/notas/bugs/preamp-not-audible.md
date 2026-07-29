---
tags: [bug, mp3player-metadata-rescue]
aliases: [**Preamp not audible**]
date: 2026-07-29
---

# Bug: **Preamp not audible**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
`syncSoftwareEq()` always called `mp.setEqPreampGain(0f)`, ignoring `currentPreamp`. The preamp was only baked into HW EQ gains, never sent to software EQ.

## Correcao
`syncSoftwareEq()` now calls `mp.setEqPreampGain(currentPreamp)` instead of `0f`. Software EQ receives preamp as a master multiplier.
