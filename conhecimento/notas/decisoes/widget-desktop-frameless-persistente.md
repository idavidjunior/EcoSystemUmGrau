---
tags: [botao, decisao, direito, opencode, redimensionamento, win]
aliases: [widget desktop frameless persistente]
date: 2026-08-04
---

# widget desktop frameless persistente

**Fonte:** opencode

Tipo: decisao

Tags: [widget, grafo, pywebview, windows, frameless, persisten, workerw, desktop]

Data: 2026-08-02

contexto: Usuario pediu o grafo do conhecimento como widget de desktop estilo Rainmeter: colado na area de trabalho, controles ocultos que surgem ao clicar com botao direito, e redimensionamento persistente.

decisao: Janela pywebview frameless ancorada atras das outras janelas via SetWindowPos HWND_BOTTOM persistente. Controles ocultos por CSS default; contextmenu no body alterna classe .desktop que revela header + alca de resize (#mk-resize) que chama bridge redimensionar(w,h)->win.resize(). Geometria persiste em JSON (docs/grafo_widget_geometria.json), carregada no create_window e re-salva por watcher + no fechamento.

impacto: Widget de desktop funcional, redimensionavel, com estado restaurado entre execucoes.
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]