---
tipo: decisao
tags: [gui, desktop, widget, edge, cerebro-vivo, ecow]
data: 2026-09-01
contexto: O usuario pediu para remover as janelas da GUI desktop (chat e HUD) e deixar o sistema "como era somente com o Edge e o cerebro vivo".
decisao: Desativada a GUI desktop (gui-desktop/main.py), que abria a janela HUD (Arc Reactor) e a janela de chat. O ecossistema passa a rodar apenas com o widget oficial Edge (scripts/widget_edge.py) e o Cerebro Vivo (scripts/widget_grafo.py, grafo 3D do conhecimento).
impacto: Nenhuma janela da GUI desktop abre mais. O Edge continua rodando e o Cerebro Vivo foi aberto via scripts/ecow.bat. As janelas de chat que nao funcionavam nao incomodam mais.
aprendizado: O widget oficial Edge e aberto por scripts/controle.bat (pythonw scripts/widget_edge.py). O Cerebro Vivo e aberto por scripts/ecow.bat (pythonw scripts/widget_grafo.py); se ja houver instancia, ela foca a janela existente e sai. A GUI desktop gui-desktop/main.py era uma adicao recente e foi desativada; ela exigia o venv .venv-gui (PyQt6).

## Conexoes

- [[2026-08-04-tamanho-por-uso-real-iniciar-gui-com-pythonw-impl]]
- [[treinamento-especializado-em-navegacao-multi-plataforma-reco]]