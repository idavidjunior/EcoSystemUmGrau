---
tags: [arestas, cognitivo, general, layout, zero, órfãs]
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

---
tipo: erro
tags: [widget, vis-network, quadtree, stack-overflow, NaN, regenerar, loop]
data: 2026-08-06
contexto: >
  O widget desktop "Cerebro Vivo" (pywebview + vis-network 9.1.9, gerado por
  scripts/generate-graph-html.py e scripts/widget_grafo.py) travava em um
  determinado momento. O log docs/widget_log.txt registrava 6x
  "Uncaught RangeError: Maximum call stack size exceeded @ 97:250114".
decisao: >
  (1) Crash do NaN: o tick handler fazia `x: n.x + orb.dx` usando n.x do
  DATASET, 

---
tipo: erro
tags: [widget, unified-bridge, auditeria, bugs, pywebview]
data: 2026-08-18
contexto: >
  Auditoria do widget Jarvis Controle (unified_bridge.py) identificou 7 bugs.
  Bug critico: ler_estado_voz() chamada mas nunca definida/importada.
  Causava NameError silencioso capturado por except:pass.
  UI nunca atualizava estado, botoes nao funcionavam.
decisao: >
  (1) Definir ler_estado_voz() lendo CONTROLE (narracao_estado.json).
  (2) Refatorar estado_ativo() para usar ler_estado_voz(

---
tipo: erro
tags: [widget, cerebro, grafo, keyerror, tipos, str-int, payload]
data: 2026-09-05
contexto: O widget "Cerebro Vivo" (scripts/widget_grafo.py + www/cerebro.html) exibia canvas em branco e seu log repetia "vigia: KeyError: 162". O grafo nunca recebia payload.
decisao: Corrigir a inconsistência de tipos de id entre nós e arestas em memories_to_widget e blindar layout_3d contra arestas órfãs.
impacto: Payload combined passou a ser enviado (1007 nós / 4869 arestas, zero arestas órfãs)
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]