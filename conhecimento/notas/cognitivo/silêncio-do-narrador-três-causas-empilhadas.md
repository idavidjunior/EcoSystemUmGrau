---
tags: [alto, cognitivo, falante, general, nada, saía]
aliases: [Silêncio do narrador — três causas empilhadas]
date: 2026-08-29
---

# Silêncio do narrador — três causas empilhadas

**Dominio:** general

---
titulo: Silencio do narrador tinha tres causas empilhadas
tipo: erro
tags: [narrador, tts, audio, resiliencia, diagnóstico]
data: 2026-08-29
---

# Silêncio do narrador — três causas empilhadas

## Contexto
O usuário relatou "não estou ouvindo o narrador". A telemetria mostrava fala ok (MP3 gerado, `ok=True`), mas nada saía no alto-falante.

## Causas encontradas (em camadas)

1. **Bug no widget**: `voice_off()` chamava `_narrador_pausar(True)` em vez de `False`. Corrigido — hoje a função re
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]