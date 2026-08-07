---
tipo: padrao
tags: [stt, whisper, streaming, partial, vad, android]
data: 2026-08-06T23:24:41
contexto: vox-audio-voxstt
decisao: Added partial result callbacks to STT pipeline
impacto: Medium - real-time transcription feedback

# Implementacao: Partial/Streaming STT Results

## Problema
1. _stt_whisper() em ox_audio.py juntava todos os segmentos do Whisper
   em um unico texto no final, sem feedback parcial.
2. VoxStt.kt no Android tinha onPartialResults vazio — resultados
   parciais do SpeechRecognizer eram descartados silenciosamente.

## Solucao
1. **vox_audio.py**:
   - _stt_whisper(audio, partial_callback=None) — nova assinatura
   - A cada segmento completado, chama partial_callback(texto_parcial)
   - Usuario ve a transcricao evoluir em tempo real no terminal

2. **VoxStt.kt**:
   - onPartialResults agora extrai RESULTS_RECOGNITION e chama onResult(text)
   - Resultado parcial exibido na UI enquanto o usuario fala

3. **dialogo.py**:
   - Import atualizado para incluir gerar_audio_stream
   - cmd_ouvir aceita partial_callback para feedback visual

## Beneficio
Reducao de percepatura de latencia: o usuario vê o texto aparecer
gradualmente ao inves de esperar o final da captura completa.
