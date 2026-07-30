---
tags: [bug, mp3player-metadata-rescue]
aliases: [User sees wrong/short results]
date: 2026-07-30
---

# Bug: User sees wrong/short results

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
Scoring rejected borderline-but-correct match

## Correcao
User taps "Tentar Novamente" in dialog → triggers RELAXED mode with lower thresholds
