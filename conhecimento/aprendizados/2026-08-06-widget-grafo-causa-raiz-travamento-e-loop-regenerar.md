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
  DATASET, que nao tem posicoes (improvedLayout falha; dataset sem x/y). No
  primeiro frame n.x era undefined -> undefined + numero = NaN ->
  nodes.update(noUpd) gravava NaN no corpo fisico -> no passo seguinte o
  quadtree Barnes-Hut (_placeInTree/_placeInRegion) recebia no com NaN,
  comparacoes sempre falsas -> recursao infinita -> stack overflow.
  Fix: ler a posicao viva via network.getPositions() e somar a deriva orbital
  somente sobre valores finitos (Number.isFinite), com fallback para 0.
  (2) Loop de regenerar: o gerador reescrevia
  conhecimento/aprendizados/cluster_mapper.json em TODA execucao; o _versao()
  do widget observa o mtime mais recente de conhecimento/* -> cada regenerar
  mudava a versao -> regenerar de novo -> reload da pagina a cada 2s.
  Fix: o gerador so grava o json quando o conteudo mudou.
impacto: >
  Widget volta a ficar vivo por periodo prolongado sem crash e sem reload
  infinito. Validado: harness Node 47/47 PASS; repro6 (200 ticks de fisica +
  tick handler corrigido) sem NaN e sem crash; widget rodando 135s+ ALIVE,
  0 erros regenerar, 0 novos stack overflows no log.

## Conexoes

- [[2026-08-04-tamanho-por-uso-real-iniciar-gui-com-pythonw-impl]]