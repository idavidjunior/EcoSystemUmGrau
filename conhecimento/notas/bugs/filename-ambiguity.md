---
tags: [bug, mp3player-metadata-rescue]
aliases: [Filename ambiguity]
date: 2026-07-29
---

# Bug: Filename ambiguity

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
Multiple filename formats

## Correcao
Try dash split first, then double-space split as fallback
