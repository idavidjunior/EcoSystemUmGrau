---
tags: [cognitivo, general, logo, parada, pipeline, speech]
aliases: [Parar Fala — corrida da flag parar_fala.flag]
date: 2026-08-21
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
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]