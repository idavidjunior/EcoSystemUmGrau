---
tags: [arquivo, bons, cognitivo, estavam, general, reprodução]
aliases: [Silêncio do narrador — três causas empilhadas]
date: 2026-08-29
---

# Silêncio do narrador — três causas empilhadas

**Dominio:** general

## Contexto
O usuário relatou "não estou ouvindo o narrador". A telemetria mostrava fala ok (MP3 gerado, `ok=True`), mas nada saía no alto-falante.

## Causas encontradas (em camadas)

1. **Bug no widget**: `voice_off()` chamava `_narrador_pausar(True)` em vez de `False`. Corrigido — hoje a função retoma o narrador.

2. **PID file órfão no tts_service**: `runtime/tts_service.pid` continha PID de processo morto. O checador `_instancia_unica()` detectava corretamente e recriava; mas kills forçados deixavam lixo. Reforçado o `finally` de cleanup e o singleton com O_EXCL.

3. **Causa final real (hardware/Windows)**: o Windows estava enviando áudio para o dispositivo errado — "TeamViewer Audio" assumiu como padrão de reprodução. Detectado ao comparar: código ok, logs ok, MP3 ok, mas som nenhum. O teste MCI direto com um MP3 do cache reproduziu sem erro, confirmando que o codec e o arquivo estavam bons.

## Verificação

- Telemetria `runtime/tts_telemetria.jsonl` mostrava `status: ok, mp3_by
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]