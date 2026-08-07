---
tags: [bug, lower, mode, mp3player-metadata-rescue, relaxed, thresholds]
aliases: [User sees wrong/short results]
date: 2026-08-07
---

# User sees wrong/short results

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
Scoring rejected borderline-but-correct match

## Correcao
User taps "Tentar Novamente" in dialog → triggers RELAXED mode with lower thresholds
## Conexoes

- [[bug-hub-bugs]]
- [[calls-searchonlinesearchmoderelaxed-uses-relaxed-thresholds-]]
- [[cluster-hub-mp3player]]
- [[if-relaxed-also-fails-user-sees-tente-editar-manualmente-os-]]
- [[step-0-acoustid-fingerprint-acoustidservicesearchbyfile-almo]]
- [[user-taps-buscar-na-internet]]