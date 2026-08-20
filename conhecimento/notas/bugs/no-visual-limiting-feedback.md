---
tags: [250ms, bug, every, handler, mp3player-metadata-rescue, polled]
aliases: [**No visual limiting feedback**]
date: 2026-08-20
---

# **No visual limiting feedback**

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
User couldn't see when limiter was active or how much reduction was applied.

## Correcao
Added `gainReductionDb` property on processor, `TextView` indicator in bottom bar (green=no reduction, yellow=moderate, red=heavy), polled every 250ms via Handler.
## Conexoes

- [[bug-hub-bugs]]
- [[calls-searchonlinesearchmoderelaxed-uses-relaxed-thresholds-]]
- [[cluster-hub-mp3player]]
- [[if-relaxed-also-fails-user-sees-tente-editar-manualmente-os-]]
- [[step-0-acoustid-fingerprint-acoustidservicesearchbyfile-almo]]
- [[user-taps-buscar-na-internet]]