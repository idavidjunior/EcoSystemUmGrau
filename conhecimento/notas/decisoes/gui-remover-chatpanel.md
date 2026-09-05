---
tags: [decisao, eco, mensagens, online, opencode, respondia]
aliases: [gui remover chatpanel]
date: 2026-09-01
---

# gui remover chatpanel

**Fonte:** opencode

Tipo: decisao

Tags: [gui, desktop, chat, pyqt6, bridge, venv]

Data: 2026-09-01

contexto: A interface desktop tinha uma janela "Conversa com Eco" (ChatPanel) que nao respondia as mensagens do usuario. O usuario pediu para remover essa funcao e voltar ao comportamento anterior.

decisao: Removida a janela ChatPanel (e TestConsole) do gui-desktop/main.py, restaurando o comportamento original que abre apenas o HUD (Arc Reactor) e conecta na bridge.

impacto: GUI abre de forma estavel novamente, conectando na bridge WebSocket (Bridge online). A janela de chat que nao funcionava nao abre mais.
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]