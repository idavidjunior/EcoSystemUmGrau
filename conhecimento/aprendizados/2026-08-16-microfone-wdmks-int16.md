# 2026-08-16: MicrofoneManager — device WDM-KS int16 e referências por import

**Categoria:** erro
**Contexto:** Implementação dos 8 passos de evolução do microfone do JARVIS (device persistente, hot-plug, wake word, streaming STT, enhancement, bridge, health check, config unificada) no EcoSystemUmGrau.

## Problema 1: float32 corrompe no driver WDM-KS

O device 11 (Microfone Realtek HD Audio Mic input, hostapi WDM-KS) entrega dados corrompidos (RMS ~1e18, NaN) quando capturado com dtype float32 via sounddevice. O mesmo device com dtype int16 entrega dados estáveis (RMS ~0.002-0.004). Todos os hostapis alternativos (MME device 1, DirectSound device 5) falham com "Unanticipated host error"; WASAPI (device 9) rejeita a abertura ("Invalid device"); pvrecorder também falha ao inicializar. O driver de áudio Realtek do Windows está degradado neste ambiente.

**Decisão:** Capturar SEMPRE com int16 e converter para float32 (divisão por 32768) antes do resample/VAD. Criado helper `_rec_bloco_f32()` no dialogo.py que tenta int16 primeiro com fallback float32. WDM-KS não dispara callbacks de streaming e não suporta blocking API (RawInputStream), então a captura usa `sd.rec` por blocos.

## Problema 2: latência do sd.rec no WDM-KS

Cada chamada `sd.rec` com bloco de 0.1s leva ~0.7s (overhead fixo de inicialização do driver). Com blocos de ~1s o overhead se dilui (4s de áudio em 4.29s real). **Decisão:** o `_alimentar_vad_bloqueante` captura blocos de ~1s e processa em chunks de 512 (32ms) para o Silero VAD.

## Problema 3: audit_triagem move módulos importados por engano

O `scripts/audit_triagem.py` detectava referências apenas pelo nome do arquivo completo (ex.: `microfone_manager.py`), mas o Python usa `from microfone_manager import ...` (sem extensão). Isso fez o módulo `microfone_manager.py` ser classificado como órfão e movido para `scripts/_legado/`, quebrando os imports de `dialogo.py` e `vox_audio.py`.

**Decisão:** `collect_reference_map()` agora pré-compila um regex de import por script (uma única vez) e detecta `from X import` / `import X`. Usa `re.search` por script apenas quando o nome completo não aparece, com regex compilado para não degradar performance. Após o fix, `microfone_manager.py` tem refs reais (`dialogo.py`, `vox_audio.py`) e `total_orfaos=0`.

## Problema 4: contrato quebrado na bridge

`jarvis_bridge.py` importava `_classificar_conexao` do `frases_manager`, mas o nome real é `classificar_conexao` (retorna str, não dict). A importação caía no fallback local, perdendo a lógica de 3 fontes. **Decisão:** importar `classificar_conexao` e criar wrapper local `_classificar_conexao()` que traduz str → dict `{eh_reconexao, minutos_desde_atividade, hist_tamanho}`.

## Impacto

- Microfone do JARVIS funciona no device 11 (WDM-KS) com int16, mas com latência inerente do driver (~0.7s overhead por bloco pequeno).
- Os 8 passos de evolução do microfone estão implementados e compilam: `config/microfone.json`, `scripts/microfone_manager.py`, `scripts/dialogo.py`, `scripts/vox_audio.py`, `scripts/widget_controle_jarvis.py`, `scripts/jarvis_bridge.py`.
- Testes: py_compile OK em 6 arquivos; integração OK (device 11 persistido, `mic_estado.json` com ativo/status/device_id/timestamp, watchdog_ok=True).
