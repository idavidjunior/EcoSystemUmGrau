---
tags: [automaticamente, cognitivo, comportamento, general, repita, vier]
aliases: [auditoria cerebro vivo fix tema padrao e bugs]
date: 2026-08-23
---

# auditoria cerebro vivo fix tema padrao e bugs

**Dominio:** general

---
tipo: erro
tags: [cerebro-vivo, grafo, widget, generate-graph-html, tema-padrao, fisica, vis-network, javascript]
data: 2026-08-13
contexto: Auditoria do widget "Cérebro Vivo" (docs/grafo.html, gerado por scripts/generate-graph-html.py).
Linha de trabalho escolhida: corrigir o tema Padrão + sanar bugs. Fase 1 mapeou estados e fluxos;
Fase 2 validou todos os blocos JS com node --check (principal 740KB + widget-extra.js + resize.js).
decisao: 1) TEMAS.padrao.forca usava as chaves {grav, centra

---
tipo: melhoria
tags: [widget-grafo, cerebro-vivo, sinapses, visualizacao, animacao]
data: 2026-08-22
contexto: Pedido do usuário de que implementações novas pisquem ativas no grafo por 12 horas, com sugestão de amarelo forte, e que o comportamento se repita automaticamente para tudo que vier depois.
---

# Sinapses Novas Pulsam em Amarelo por 12 Horas no Cerebro Vivo

## Decisão
O payload do widget_grafo.py passou a carregar tm (epoch do mtime da nota) em cada nó. O cerebro.html avalia a ida
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]