---
tags: [cognitivo, general, passou, pausado, retomar, retornar]
aliases: [Reverter as mudancas do Cerebro e implementar Pausar/Retomar]
date: 2026-09-05
---

# Reverter as mudancas do Cerebro e implementar Pausar/Retomar no Edge. 

**Dominio:** general

Tipo: decisao

Tags: [narrador, edge, widget, pausa, cerebro]

Data: 2026-08-28

contexto: Pedido de botao pausar/parar no widget. A primeira implementacao foi colocada no Cerebro Vivo (www/cerebro.html + widget_grafo.py), mas o alvo correto era a janela Edge (widget_edge.py), onde roda o motor de narracao.

decisao: Reverter as mudancas do Cerebro e implementar Pausar/Retomar no Edge. EdgeApi ganhou pause()/resume() e status() passou a retornar pausado. UI www/index.html ganhou o botao btnPaus
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]