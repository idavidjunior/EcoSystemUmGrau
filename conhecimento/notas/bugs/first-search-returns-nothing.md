---
tags: [bug, mp3player-metadata-rescue]
aliases: [First search returns nothing]
date: 2026-08-01
---

# Bug: First search returns nothing

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
Wrong artist extracted from filename, or title too noisy

## Correcao
Auto-fallback: NORMAL→RELAXED auto-retry; RELAXED tries title-only and artist-only queries
