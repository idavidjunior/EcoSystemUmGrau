---
tags: [bug, filename, mp3player-metadata-rescue, noisy, projeto, queries]
aliases: [First search returns nothing]
date: 2026-08-05
---

# First search returns nothing

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
Wrong artist extracted from filename, or title too noisy

## Correcao
Auto-fallback: NORMAL→RELAXED auto-retry; RELAXED tries title-only and artist-only queries
## Conexoes

- [[bug-hub-bugs]]
- [[calls-searchonlinesearchmoderelaxed-uses-relaxed-thresholds-]]
- [[cluster-hub-mp3player]]
- [[if-relaxed-also-fails-user-sees-tente-editar-manualmente-os-]]
- [[step-0-acoustid-fingerprint-acoustidservicesearchbyfile-almo]]
- [[user-taps-buscar-na-internet]]