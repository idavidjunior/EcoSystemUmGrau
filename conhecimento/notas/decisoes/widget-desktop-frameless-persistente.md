---
tags: [decisao, filha, opencode, proprias, reparent, resistem]
aliases: [widget desktop frameless persistente]
date: 2026-08-13
---

# widget desktop frameless persistente

**Fonte:** opencode

---
tipo: decisao
tags: [widget, grafo, pywebview, windows, frameless, persisten, workerw, desktop]
data: 2026-08-02
contexto: Usuario pediu o grafo do conhecimento como widget de desktop estilo Rainmeter: colado na area de trabalho, controles ocultos que surgem ao clicar com botao direito, e redimensionamento persistente.
decisao: Janela pywebview frameless ancorada atras das outras janelas via SetWindowPos HWND_BOTTOM persistente. Controles ocultos por CSS default; contextmenu no body alterna classe .desktop que revela header + alca de resize (#mk-resize) que chama bridge redimensionar(w,h)->win.resize(). Geometria persiste em JSON (docs/grafo_widget_geometria.json), carregada no create_window e re-salva por watcher + no fechamento.
impacto: Widget de desktop funcional, redimensionavel, com estado restaurado entre execucoes. 
licoes: (1) Ancoragem Progman/WorkerW (SetParent p/ WorkerW) NAO funciona com WebView2 (EdgeChromium) - WebView2 cria janelas-filha proprias que resistem ao reparent; parent fica None; usar HWND_BOTTOM + re-baixamento continuo. (2) FindWindowW(None,title) pode retornar 0 para janelas ancoradas; preferir EnumWindows por classe/processo. (3) ctypes.wintypes e usado via 'from ctypes import wintypes', nao 'ctypes.wintypes'. (4) frameless sem moldura exige alca custom em JS para redimensionar pois nao ha handle nativa.
uso: python scripts/widget_grafo.py
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]