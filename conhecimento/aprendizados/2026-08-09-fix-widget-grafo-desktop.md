---
tipo: padrao
tags: [widget, grafo, pywebview, vis-network, fix]
data: 2026-08-09
contexto: Varedura do widget desktop "Cerebro Vivo" (scripts/widget_grafo.py) identificou 8 problemas; todos corrigidos.
decisao: Substituir polling JS (api-inject.js) por watcher Python com lock; criar handles mk-drag/mk-resize via resize.js injetado no body; bridge expoe mover/redimensionar; tema via CSS vars + data-theme; guardar_geo ignora (0,0) e clampeia a tela.
impacto: Widget agora move/redimensiona de verdade, reflete mudancas do vault ao vivo, nao tem reload em loop, tema tem efeito real e geometria nunca sai da tela.
notas:
  - resize.js era lido (RESIZE_JS) mas nunca injetado em _build_view -> alca inexistente.
  - #mk-drag nunca era criado por nenhum script; easy_drag=False -> janela imovel.
  - window.location.reload() no polling recarregava HTML estatico sem regenerar e, como lastTs resetava no reload, gerava reload em loop.
  - Seletor de tema so setava data-theme sem nenhum CSS/JS reagir.
  - guardar_orbGrafo/ORB_FILE eram bridge morta; orbita persistia 3.00 num arquivo que nada lia.
  - Removidos ~130 artefatos de debug (scripts/_backup_debug_temp, check_*.py, debug_*.py, _test_*.js, gg.js, api-inject.js, orbGrafo.json).
  - pywebview 6.2.1: Window.move/resize/evaluate_js disponiveis; nao ha propriedades x/y/width/height diretas (geometria via JS window.screenX/innerWidth).
