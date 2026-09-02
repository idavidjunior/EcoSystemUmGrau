---
tags: [decisao, mensagens, online, opencode, ping, respondia]
aliases: [gui remover chatpanel]
date: 2026-09-01
---

# gui remover chatpanel

**Fonte:** opencode

---
tipo: decisao
tags: [gui, desktop, chat, pyqt6, bridge, venv]
data: 2026-09-01
contexto: A interface desktop tinha uma janela "Conversa com Eco" (ChatPanel) que nao respondia as mensagens do usuario. O usuario pediu para remover essa funcao e voltar ao comportamento anterior.
decisao: Removida a janela ChatPanel (e TestConsole) do gui-desktop/main.py, restaurando o comportamento original que abre apenas o HUD (Arc Reactor) e conecta na bridge.
impacto: GUI abre de forma estavel novamente, conectando na bridge WebSocket (Bridge online). A janela de chat que nao funcionava nao abre mais.
aprendizado: (1) A GUI desktop DEVE ser aberta com o venv ".venv-gui", que tem o PyQt6 instalado. O python global nao tem PyQt6 e faz a GUI falhar com ModuleNotFoundError. (2) O pacote gui-desktop usa hifen no nome, entao o main.py precisa do mecanismo de carga via importlib (nome canonico gui_desktop.*); sem isso ocorre "No module named gui_desktop". (3) A bridge (porta 8765) e o serve (8767) estao saudaveis: o serve autentica com HTTP 200 usando user 'opencode' e a bridge responde ping via WebSocket.
 // ---
tipo: decisao
tags: [gui, desktop, chat, pyqt6, bridge, venv]
data: 2026-09-01
contexto: A interface desktop tinha uma janela "Conversa com Eco" (ChatPanel) que nao respondia as mensagens do usuario. O usuario pediu para remover essa funcao e voltar ao comportamento anterior.
decisao: Removida a janela ChatPanel (e TestConsole) do gui-desktop/main.py, restaurando o comportamento original que abre apenas o HUD (Arc Reactor) e conecta na bridge.
impacto: GUI abre de forma estavel novamente, conectando na bridge WebSocket (Bridge online). A janela de chat que nao funcionava nao abre mais.
aprendizado: (1) A GUI desktop DEVE ser aberta com o venv ".venv-gui", que tem o PyQt6 instalado. O python global nao tem PyQt6 e faz a GUI falhar com ModuleNotFoundError. (2) O pacote gui-desktop usa hifen no nome, entao o main.py precisa do mecanismo de carga via importlib (nome canonico gui_desktop.*); sem isso ocorre "No module named gui_desktop". (3) A bridge (porta 8765) e o serve (8767) estao saudaveis: o serve autentica com HTTP 200 usando user 'opencode' e a bridge responde ping via WebSocket.

## Conexoes

- [[treinamento-especializado-em-navegacao-multi-plataforma-reco]]
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]