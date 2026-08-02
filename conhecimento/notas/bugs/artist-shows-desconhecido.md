---
tags: [bug, mp3player-metadata-rescue]
aliases: [Artist shows "Desconhecido"]
date: 2026-08-01
---

# Artist shows "Desconhecido"

**Projeto:** mp3player-metadata-rescue

## Causa Raiz
YouTube MP3s have no ID3 tags

## Correcao
Extract artist from filename (first dash segment or second double-space segment)
## Conexoes

- [[bug-hub-bugs]]
- [[calls-searchonlinesearchmoderelaxed-uses-relaxed-thresholds-]]
- [[cluster-hub-mp3player]]
- [[if-relaxed-also-fails-user-sees-tente-editar-manualmente-os-]]
- [[step-0-acoustid-fingerprint-acoustidservicesearchbyfile-almo]]
- [[user-taps-buscar-na-internet]]