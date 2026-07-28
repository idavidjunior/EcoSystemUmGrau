---
tags: [bug, mp3player-metadata-rescue]
aliases: [Artist shows "Desconhecido"]
date: 2026-07-28
---

# Bug: Artist shows "Desconhecido"

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
YouTube MP3s have no ID3 tags

## Correcao
Extract artist from filename (first dash segment or second double-space segment)
