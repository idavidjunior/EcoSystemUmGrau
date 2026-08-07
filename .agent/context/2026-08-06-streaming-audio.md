---
tipo: padrao
tags: [streaming, audio, tts, websocket, edge-tts]
data: 2026-08-06T23:24:41
contexto: bridge-jarvis-vox
decisao: Implemented incremental audio streaming via async generator
impacto: Medium - improved UX, text displays immediately

# Implementacao: Streaming Audio via WebSocket

## Problema
gerar_audio() em jarvis_bridge.py blocaba ate a geracao completa do TTS
pelo edge-tts, depois enviava um unico blob base64 grande. O cliente Android
so via o texto e o audio simultaneamente, mas so podia tocar depois que
o audio inteiro era recebido.

## Solucao
1. **jarvis_bridge.py**: Nova funcao gerar_audio_stream(texto) — async generator
   que yield chunks base64 a medida que o edge-tts gera.

2. **ws_responder**: Protocolo de streaming:
   - Envia {{text, corrigido, audio_streaming: True}} — texto imediato
   - Envia {{audio_chunk: <b64>}} para cada chunk gerado
   - Envia {{audio_done: True}} para finalizar

3. **VoxAudioPlayer.kt (Android)**:
   - startStream() — cria temp file para acumular chunks
   - playChunk(b64) — append ao arquivo incrementalmente
   - inishStream() — toca o arquivo completo
   - cancelStream() — limpa em caso de erro/desconexao

4. **VoxViewModel.kt (Android)**:
   - Estado udioStreaming para tracking
   - Handler para udio_streaming, udio_chunk, udio_done
   - Texto exibido imediatamente, audio tocado quando completo

## Backward Compatibility
O cliente antigo ainda funciona com {text, audio, corrigido} em uma unica
mensagem (path mantido no handler).
