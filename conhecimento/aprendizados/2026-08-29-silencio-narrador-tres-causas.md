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

1. **Bug no widget**: `voice_off()` chamava `_narrador_pausar(True)` em vez de `False`. Corrigido — hoje a função retoma o narrador.

2. **PID file órfão no tts_service**: `runtime/tts_service.pid` continha PID de processo morto. O checador `_instancia_unica()` detectava corretamente e recriava; mas kills forçados deixavam lixo. Reforçado o `finally` de cleanup e o singleton com O_EXCL.

3. **Causa final real (hardware/Windows)**: o Windows estava enviando áudio para o dispositivo errado — "TeamViewer Audio" assumiu como padrão de reprodução. Detectado ao comparar: código ok, logs ok, MP3 ok, mas som nenhum. O teste MCI direto com um MP3 do cache reproduziu sem erro, confirmando que o codec e o arquivo estavam bons.

## Verificação

- Telemetria `runtime/tts_telemetria.jsonl` mostrava `status: ok, mp3_bytes > 0`.
- Teste de beep do console (`[console]::beep`) saía.
- Teste MCI direto (`mciSendStringW play`) funcionou.
- Apenas o dispositivo de destino do Windows estava errado.

## Correção / Resiliência adotada

- `voice_off()` retoma o narrador (sem pausa órfã).
- Narrador tem heartbeat em `runtime/narrador_heartbeat.json`.
- Poller do widget vigiando heartbeat: reinicia thread se parar.
- Boot do widget normaliza `narracao_estado.json` (despausa automaticamente).
- TTS Service com singleton (O_EXCL), PID file limpo na saída e log em arquivo (`runtime/tts_service.log`).

## Regra aprendida

Quando telemetria diz que o processamento/saída foi ok mas o usuário relata ausência de resultado, suspeitar primeiro da camada *fora* do código: dispositivo de reprodução padrão, volume master, ro一事teamento de saída. Verificar `control mmsys.cpl` antes de culpar o código.

## Possível melhoria futura

Adicionar ao preflight uma checagem do dispositivo de saída de áudio padrão e alerta se não for o hardware esperado.
