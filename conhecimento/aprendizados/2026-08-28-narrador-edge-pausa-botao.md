---
tipo: decisao
tags: [narrador, edge, widget, pausa, cerebro]
data: 2026-08-28
contexto: Pedido de botao pausar/parar no widget. A primeira implementacao foi colocada no Cerebro Vivo (www/cerebro.html + widget_grafo.py), mas o alvo correto era a janela Edge (widget_edge.py), onde roda o motor de narracao.
decisao: Reverter as mudancas do Cerebro e implementar Pausar/Retomar no Edge. EdgeApi ganhou pause()/resume() e status() passou a retornar pausado. UI www/index.html ganhou o botao btnPausa (pisca quando pausado) e usa o botao Parar que ja existia.
impacto: Controles ficam onde o narrador opera; Cerebro Vivo ficou limpo para a futura atualizacao. Estado via narracao_estado.json + parar_fala.flag continua como fonte unica.
