---
tags: [cognitivo, general, marcava, parada, pipeline, websocket]
aliases: [Parar Fala — corrida da flag parar_fala.flag]
date: 2026-08-13
---

# Parar Fala — corrida da flag parar_fala.flag

**Dominio:** general

---
tipo: erro
tags: [widget, narrador, parar-fala, flag, corrida, tts, jarvis, speech-pipeline]
data: 2026-08-13
contexto: Botão "Parar Fala" do widget Jarvis não parava a narração; usuário relatou que Jarvis continuava falando após acionar o botão.
decisao: cmd_interromper_fala (scripts/widget_controle_jarvis.py) passou a manter a flag runtime/parar_fala.flag por 1.5s antes de apagá-la, e removeu o feedback de áudio "Voz desativada" que era falado logo após a parada.
impacto: Narrador em proce

---
tipo: erro
tags: [cerebro-vivo, fala, jarvis-bridge, dialogo, retrato, widget]
data: 2026-08-28
contexto: O usuário pediu que os efeitos do Cérebro Vivo acendessem enquanto o Eco fala por voz. Ao auditar, descobriu-se que a região de fala nunca acendia na prática.
decisao: O jarvis_bridge.py gerava TTS (edge-tts) e enviava o áudio ao app via WebSocket, mas NUNCA marcava runtime/dialogo_vivo.json nem emitia a atividade "fala". Apenas scripts/dialogo.py (modo VAD, que não roda no PC quando se 
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]