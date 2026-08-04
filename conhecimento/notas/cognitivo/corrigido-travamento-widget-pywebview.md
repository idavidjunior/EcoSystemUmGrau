---
tags: [cognitivo, dispara, general, infinita, processing, while]
aliases: [corrigido travamento widget pywebview]
date: 2026-08-04
---

# corrigido travamento widget pywebview

**Dominio:** general

---
tipo: erro
tags: [widget, pywebview, windows, travamento, recursao, debug, frameless]
data: 2026-08-02
contexto: O widget desktop do grafo (scripts/widget_grafo.py) travava; o terminal python mostrava recorrente `[pywebview] Error while processing win.native.AccessibilityObject.Bounds.Empty...: maximum recursion depth exceeded`.
decisao: Duas causas distintas atacadas:
1. GEOMETRIA: ler `win.x/win.y/win.width/win.height` a partir de thread nao-principal (loop de 1s) dispara recursao infinita
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]