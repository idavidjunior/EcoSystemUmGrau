---
tipo: decisao
tags: [grafo, cerebro-vivo, vis-network, conhecimento, clusters, conexoes]
data: 2026-08-02
contexto: Grafo do conhecimento (docs/grafo.html) tinha 226 nos, 1460 arestas, mas 0 arestas entre clusters — 67 componentes conexos, clusters isolados (cognicao inteira solta).
decisao: Adicionei ao gerador (scripts/generate-graph-html.py) um passo de pontes curadas BRIDGES_CLUSTERS + ancora do hub de cognicao ligado a todos os demais hubs. Cada ponte e (fragA, fragB) onde cada fragmento deve casar EXATAMENTE um no; caso contrario a ponte e ignorada com aviso, nunca aborta a geracao (principio fail-safe).
impacto: 13 pontes criadas (0 descartadas), 12 arestas inter-cluster (antes 0), pares de clusters conectados 0->7, componentes conexos 67->55. Sem bits de dados, apenas nova passada de conexoes curadas.
uso: python scripts/generate-graph-html.py docs/grafo.html
