---
tags: [bug, mp3player-metadata-rescue]
aliases: [**No visual limiting feedback**]
date: 2026-08-01
---

# Bug: **No visual limiting feedback**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
User couldn't see when limiter was active or how much reduction was applied.

## Correcao
Added `gainReductionDb` property on processor, `TextView` indicator in bottom bar (green=no reduction, yellow=moderate, red=heavy), polled every 250ms via Handler.
