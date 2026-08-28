---
tipo: erro
tags: [cerebro-vivo, fala, jarvis-bridge, dialogo, retrato, widget]
data: 2026-08-28
contexto: O usuário pediu que os efeitos do Cérebro Vivo acendessem enquanto o Eco fala por voz. Ao auditar, descobriu-se que a região de fala nunca acendia na prática.
decisao: O jarvis_bridge.py gerava TTS (edge-tts) e enviava o áudio ao app via WebSocket, mas NUNCA marcava runtime/dialogo_vivo.json nem emitia a atividade "fala". Apenas scripts/dialogo.py (modo VAD, que não roda no PC quando se usa o app) fazia essa marcação. Implementado no bridge o helper _retrato_fala/_marcar_inicio_fala: grava o retrato de forma atômica (estado "falando"/"ouvindo" + quando) e emite fala 0.95/0.0 via atividade_emit, com task agendada (asyncio) para zerar o estado após duração estimada (len(texto) * 0.055s). Aplicado na saudação, continuidade, retomada, interrupção e resposta principal (streaming).
impacto: O widget (widget_grafo.py eco_sentinela lendo dialogo_vivo.json + atividade/fala.json) agora acende a região de fala em tempo real quando o bridge fala de verdade. Validação com event loop rodando confirmou retrato "falando" -> "ouvindo" e fala 0.95 -> 0.0.

## Conexoes

- [[2026-08-04-tamanho-por-uso-real-iniciar-gui-com-pythonw-impl]]
- [[pronúncia-járvis-escrita-sem-acento-fala-com-acento]]