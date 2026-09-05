---
tags: [cognitivo, falando, general, parava, percepção, reforçava]
aliases: [Parar Fala — corrida da flag parar_fala.flag]
date: 2026-08-13
---

# Parar Fala — corrida da flag parar_fala.flag

**Dominio:** general

## Contexto

Usuário relatou que o botão "Parar Fala" do widget Jarvis não parava a fala.

## Causa raiz

1. **Corrida da flag:** `cmd_interromper_fala` (scripts/widget_controle_jarvis.py) gravava `runtime/parar_fala.flag` e a apagava na mesma função, em microssegundos. O `SpeechPipeline.speak()` do narrador (em processo, scripts/narrador_desktop.py:205) só checa a flag a cada 0.05s (tts/speech_pipeline.py:397). Se o polling não acertava aquele instante, a fala continuava.
2. **`jarvis_audio.py stop` não para o narrador em processo:** só mata subprocessos `vox_audio.py falar`. A parada real do narrador depende da flag, não do comando stop.
3. **Feedback de áudio:** o widget falava "Voz desativada" logo após parar — reforçava a percepção de que continuava falando.

## Correção aplicada

- `cmd_interromper_fala` mantém a flag por 1.5s antes do `unlink` (o narrador a consome via `stop_flag.unlink` ao detectar).
- Removido `falar_direto("Voz desativada")`; substituído por log em texto.

##
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]