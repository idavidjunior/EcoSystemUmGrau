---
tipo: decisao
tags: [vad, vox, stt, dialogo, audio, consolidacao]
data: 2026-09-06
contexto: >
  O dialogo.py e o vox_audio.py mantinham captura de voz paralela (VAD local no
  dialogo + gravacao fixa de 7s no vox_audio). Isso duplicava logica e gerava
  caminhos paralelos, violando a clausula de estrutura redundante.
decisao: >
  Consolidar TODO o VAD num unico modulo (scripts/vad_captura.py) e fazer o
  vox_audio._gravar_audio ser VAD-first com fallback fixo preservado
  (_gravar_fixo) e chave VOX_FORCE_FIXED=1 para testes deterministicos.
impacto: >
  eliminacao da duplicacao; resultado compilado em 3 modulos (py_compile OK);
  comportamento auditivo depende de validacao real do microfone/device pelo
  usuario; import circular evitado via modulo neutro (dialogo importa vox_audio).
decisoes_relacionadas:
  - MicrofoneManager nao e singleton; instancia lazy _mm no modulo e segura.
  - vox_audio nao tem MAX_FALA (so RECORD_SECONDS); nao referenciar MAX_FALA la.
---

# VAD consolidado em vad_captura + vox_audio VAD-first (2026-09-06)

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
   p/ evitar carga no module-level), fallback _gravar_fixo(seconds) original se
   falhar, e VOX_FORCE_FIXED=1 para testes deterministicos.
4. Import circular tratado: dialogo importa vox_audio (linha 40); o compartilhamento
   do VAD agora passa por vad_captura (neutro) com import local em vox_audio.

## Verificacao
- `python -m py_compile` OK em dialogo.py, vad_captura.py, vox_audio.py.
- `python -c "import vox_audio, vad_captura"` OK (18s import; module-level carrega
  SpeechPipeline). VAD_MIN_SILENCE_MS=800 (int(SILENCIO*1000)).
- Feedback compativel: on_rms recebe prob no modo Silero e rms/0.08 no fallback.
- AMBIGUIDADE RESIDUAL: validacao auditiva real (falar > silencionar > receber
  transcricao curta) nao esta verificavel nesta maquina — depende de device/hardware.
- Nao referenciar MAX_FALA em vox_audio (inexistente la).