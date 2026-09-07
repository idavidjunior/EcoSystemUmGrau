---
tags: [2026, decisao, entrada, nativa, opencode, taxa]
aliases: [VAD consolidado em vad_captura + vox_audio VAD-first (2026-0]
date: 2026-09-06
---

# VAD consolidado em vad_captura + vox_audio VAD-first (2026-09-06)

**Fonte:** opencode

## Observado
- `scripts/dialogo.py` tinha VAD completo local (streaming Silero/VADIterator,
  captura bloqueante int16 p/ WDM-KS, fallback RMS, selecao de device) e
  `scripts/vox_audio.py` gravava fixo 7s. Duplicacao clara: dois motores de turno.

## Decisao
1. Novo modulo `scripts/vad_captura.py` = fonte unica: constants (THRESHOLD,
   SILENCIO, MAX_FALA), `_manager` lazy, `rms`, `device_entrada`, `taxa_nativa`,
   `resample_para_16k`, `rec_bloco_f32`, `VadSileroStream`, `capturar_turno`
   (streaming -> bloqueante -> fallback RMS), `capturar_turno_rms_fallback`.
2. `dialogo.py`: removidas defs locais (_rms, _device_entrada, _taxa_nativa,
   _resample_para_16k, _SILERO, _carregar_silero, VadSileroStream, _rec_bloco_f32,
   _alimentar_vad_bloqueante, antigo capturar_vad, _capturar_vad_fallback) e
   passou a importar alias apenas p/ o que usa no wake word e push-to-talk.
3. `vox_audio._gravar_audio`: wrapper VAD-first -> capturar_turno() (import local
   p/ evitar carga no module-leve
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]