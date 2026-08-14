---
tipo: erro
tags: [widget, narrador, parar-fala, flag, corrida, tts, jarvis, speech-pipeline]
data: 2026-08-13
contexto: Botão "Parar Fala" do widget Jarvis não parava a narração; usuário relatou que Jarvis continuava falando após acionar o botão.
decisao: cmd_interromper_fala (scripts/widget_controle_jarvis.py) passou a manter a flag runtime/parar_fala.flag por 1.5s antes de apagá-la, e removeu o feedback de áudio "Voz desativada" que era falado logo após a parada.
impacto: Narrador em processo (SpeechPipeline.speak com stop_flag) detecta a flag no polling de 0.05s e interrompe o MCI; percepção de "continua falando" eliminada.
---

# Parar Fala — corrida da flag parar_fala.flag

## Contexto

Usuário relatou que o botão "Parar Fala" do widget Jarvis não parava a fala.

## Causa raiz

1. **Corrida da flag:** `cmd_interromper_fala` (scripts/widget_controle_jarvis.py) gravava `runtime/parar_fala.flag` e a apagava na mesma função, em microssegundos. O `SpeechPipeline.speak()` do narrador (em processo, scripts/narrador_desktop.py:205) só checa a flag a cada 0.05s (tts/speech_pipeline.py:397). Se o polling não acertava aquele instante, a fala continuava.
2. **`jarvis_audio.py stop` não para o narrador em processo:** só mata subprocessos `vox_audio.py falar`. A parada real do narrador depende da flag, não do comando stop.
3. **Feedback de áudio:** o widget falava "Voz desativada" logo após parar — reforçava a percepção de que continuava falando.

## Correção aplicada

- `cmd_interromper_fala` mantém a flag por 1.5s antes do `unlink` (o narrador a consome via `stop_flag.unlink` ao detectar).
- Removido `falar_direto("Voz desativada")`; substituído por log em texto.

## Validação

- `python -c "import ast; ast.parse(...)"` → sintaxe OK.
- `python scripts/preflight_check.py` → TODOS os testes passaram (13/13 MCP, voz guarda OK).

## Lição

Flag de interrupção nunca deve ser criada e apagada na mesma sequência quando o consumidor faz polling em intervalo maior. Manter a flag viva por janela maior que o intervalo do polling garante a detecção.
