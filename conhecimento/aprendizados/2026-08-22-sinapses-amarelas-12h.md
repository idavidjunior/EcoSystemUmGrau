---
tipo: melhoria
tags: [widget-grafo, cerebro-vivo, sinapses, visualizacao, animacao]
data: 2026-08-22
contexto: Pedido do usuário de que implementações novas pisquem ativas no grafo por 12 horas, com sugestão de amarelo forte, e que o comportamento se repita automaticamente para tudo que vier depois.
---

# Sinapses Novas Pulsam em Amarelo por 12 Horas no Cerebro Vivo

## Decisão
O payload do widget_grafo.py passou a carregar tm (epoch do mtime da nota) em cada nó. O cerebro.html avalia a idade pelo relógio local: nós com menos de 12 horas pulsam em amarelo forte (#FFD60A com brilho #FFEA00), com raio oscilando e glow animado; após 12 horas assentam na cor normal sem precisar de rebuild.

## Impacto
Qualquer nota nova no vault — incluindo os espelhos automáticos das memórias do memory_engine — nasce piscando sozinha. O cérebro vivo passa a mostrar visualmente o que é recente versus consolidado. Primeira validação: nota cli-anything-internalizado-como-habilidade-soberana pulsando 0h após o deploy.

## Detalhe técnico importante
Cache de payload foi invalidado preservando _pos para que a primeira carga já trouxesse timestamps sem perder as posições aprendidas do layout 3D.
