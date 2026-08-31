---
tipo: decisao
tags: [jarvis, gui-desktop, pyqt6, arc-reactor, reaproveitamento, spidertje/jarvis-pyqt]
data: 2026-08-31
contexto: "Usuário pediu referência externa de Jarvis com GUI validada para integrar como GUI desktop do EcoSystemUmGrau. Restrição: desktop (sem Android/web). Combinação escolhida: PyQt6 nativo (janela + overlay frameless on-top)."
decisao: "Adotar spidertje/jarvis-pyqt como referência de implementação. Reaproveitar padrões de HUD (Arc Reactor 60fps), state machine (idle/listening/thinking/speaking), SentenceBuffer para streaming TTS, barge-in RMS e agent loop async. Descartar Wyoming/LAN, MariaDB e face recognition — incompatíveis com o ecossistema local-first."
impacto: "Cria novo módulo gui-desktop/ dentro de EcoSystemUmGrau com responsabilidade única: GUI desktop do Jarvis. Integra via WebSocket com a bridge existente (ws://localhost:8765). TTS/STT reusam edge-tts e faster-whisper já presentes. Wake word fica opcional — não substitui a palavra-gatilho 'Eco' da Constituição."
alternativas_descartadas:
  - "rajatsaxena/Jarvis-GUI (Python, 12 stars, 2017): antigo, só gestos, sem state machine."
  - "ostepan8/jarvis-qml-gui (QML): pouca comunidade, sem arquitetura async."
  - "Desenvolver do zero: viola princípio de não reinventar; a referência tem código testado e pronto."
referencias:
  - repo: "https://github.com/spidertje/jarvis-pyqt"
  - arquivos_copiados: ["hud_overlay.py", "state.py", "streaming.py", "barge_in.py"]
  - arquivos_adaptados: ["wake_word.py (opcional)", "agent.py (skeleton)"]
  - arquivos_descartados: ["profile.py (MariaDB)", "face.py (OpenCV LBPH)", "stt.py/tts.py (Wyoming LAN)"]
proximo_passo: "Criar gui-desktop/ com estrutura core/, ui/, audio/, chat/, tests/. Implementar agent_bridge.py como cliente WebSocket da bridge. Validar contra preflight_check.py antes de qualquer deploy."

## Conexoes

- [[aprendizado-2026-07-31-horas-faladas-corretamente-no-tts-do-]]