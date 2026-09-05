---
tags: [agent, async, decisao, loop, opencode, rms]
aliases: [jarvis gui desktop referencia]
date: 2026-08-30
---

# jarvis gui desktop referencia

**Fonte:** opencode

Tipo: decisao

Tags: [jarvis, gui-desktop, pyqt6, arc-reactor, reaproveitamento, spidertje/jarvis-pyqt]

Data: 2026-08-31

contexto: "Usuário pediu referência externa de Jarvis com GUI validada para integrar como GUI desktop do EcoSystemUmGrau. Restrição: desktop (sem Android/web). Combinação escolhida: PyQt6 nativo (janela + overlay frameless on-top)."

decisao: "Adotar spidertje/jarvis-pyqt como referência de implementação. Reaproveitar padrões de HUD (Arc Reactor 60fps), state machine (idle/listening/thinking/speaking), SentenceBuffer para streaming TTS, barge-in RMS e agent loop async. Descartar Wyoming/LAN, MariaDB e face recognition — incompatíveis com o ecossistema local-first."

impacto: "Cria novo módulo gui-desktop/ dentro de EcoSystemUmGrau com responsabilidade única: GUI desktop do Jarvis. Integra via WebSocket com a bridge existente (ws://localhost:8765). TTS/STT reusam edge-tts e faster-whisper já presentes. Wake word fica opcional — não substitui a palavra-gatilho 'Eco' 
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]