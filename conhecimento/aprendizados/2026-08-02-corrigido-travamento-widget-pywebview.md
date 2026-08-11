---
tipo: erro
tags: [widget, pywebview, windows, travamento, recursao, debug, frameless]
data: 2026-08-02
contexto: O widget desktop do grafo (scripts/widget_grafo.py) travava; o terminal python mostrava recorrente `[pywebview] Error while processing win.native.AccessibilityObject.Bounds.Empty...: maximum recursion depth exceeded`.
decisao: Duas causas distintas atacadas:
1. GEOMETRIA: ler `win.x/win.y/win.width/win.height` a partir de thread nao-principal (loop de 1s) dispara recursao infinita no pywebview 6 winforms, pois essas propriedades resolvem via `win.native.AccessibilityObject.Bounds`. Trocado por report via JS (`window.screenX/screenY/outerWidth/outerHeight`) chamando `bridge.guardarGeo()`, persistindo JSON no Python e em `win.evaluate_js()` no fechamento.
2. ANCORAGEM: a manutencao continua de z-order (`SetWindowPos HWND_BOTTOM` em loop de 1s) reagia o problema. Mudado para ancoragem one-shot (unico `SetParent` em WorkerW) sem loop.
impacto: Widget vive >16s de forma estavel. Nota: ainda aparece 1 log UNICO (~6KB) `AccessibilityObject.Bounds.Empty.Empty...` ao abrir janela frameless - e warning benigno do pywebview que NAO trava (widget permanece vivo). Tambem validou-se que frameless sozinho gera esse 1 log (teste minimal T FL), logo nao e causa do travamento.
uso: python scripts/widget_grafo.py
