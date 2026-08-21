---
tags: [artist, bug, mp3player-metadata-rescue, projeto, results, wrong]
aliases: [Search returns wrong artist]
date: 2026-08-21
---

# Search returns wrong artist

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
iTunes BR returns irrelevant results

## Correcao
Scoring threshold system: NORMAL min=5/3, RELAXED min=3/2
## Conexoes

- [[bug-hub-bugs]]
- [[calls-searchonlinesearchmoderelaxed-uses-relaxed-thresholds-]]
- [[cluster-hub-mp3player]]
- [[if-relaxed-also-fails-user-sees-tente-editar-manualmente-os-]]
- [[step-0-acoustid-fingerprint-acoustidservicesearchbyfile-almo]]
- [[user-taps-buscar-na-internet]]