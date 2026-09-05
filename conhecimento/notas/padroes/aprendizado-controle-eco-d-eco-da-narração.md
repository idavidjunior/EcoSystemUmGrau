---
tags: [derrubar, existência, opencode, padrao, tts, usa]
aliases: [Aprendizado: Controle Eco / D Eco da narração]
date: 2026-08-10
---

# Aprendizado: Controle Eco / D Eco da narração

**Fonte:** opencode

## Resumo

Palavras-gatilho para ligar/pausar a narração do Jarvis no desktop, sem derrubar
o processo.

## Mecanismo

- `scripts/jarvis_audio.py on|off|status` — grava `runtime/narracao_estado.json`.
- `narrador_desktop.py` lê o controle a cada loop: `{"ativo": false}` pausa
  (avança a posição para não narrar backlog quando voltar).
- `on` garante o processo rodando (PID em `runtime/narrador.pid`, checado via
  `tasklist /FI "PID eq X"`).

## Lições

- Controle por arquivo de estado é mais robusto que matar o processo.
- No Windows, `os.kill(pid, 0)` não é confiável para checar existência (usa
  TerminateProcess para sinais não-CTRL); `tasklist` resolve.

## Conexoes

- [[aprendizado-2026-07-31-horas-faladas-corretamente-no-tts-do-]]
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]