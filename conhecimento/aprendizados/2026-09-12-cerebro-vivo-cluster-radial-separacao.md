---
tipo: padrao
tags: [cerebro-vivo, layout-3d, cluster-visual, agentes, separacao-radial]
data: 2026-09-12
contexto: Usuário pediu para destacar o cluster "agentes" no Cérebro Vivo (widget_grafo.py), afastando-o radialmente do centro do grafo para criar separação visual clara.
decisao: No layout_3d(), após agrupar região de fala, adicionar passo que identifica nós com cl=='agentes', calcula vetor centro-global → centroide-do-cluster, e expande cada nó nessa direção radial (fator 0.8 da distância ao centro). Mínimo 3 nós para ativar.
impacto: Cluster agentes (22 nós + 1 hub, cor roxa #e066ff) fica na periferia do grafo, visualmente separado do miolo central. Estrutura interna preservada.
reutilizavel: Sim. Para qualquer cluster: adicionar bloco similar no layout_3d() filtrando por cl=='nome_cluster', ajustar fator de expansão (0.8) e mínimo de nós (3).