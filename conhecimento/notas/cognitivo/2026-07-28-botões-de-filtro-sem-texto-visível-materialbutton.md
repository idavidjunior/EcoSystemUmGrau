---
tags: [cognitivo, fisica, general, labels, vivo, zoom]
aliases: [# 2026-07-28: Botões de filtro sem texto visível — MaterialB]
date: 2026-08-23
---

# # 2026-07-28: Botões de filtro sem texto visível — MaterialButton vs TextView

**Dominio:** general

# 2026-07-28: Botões de filtro sem texto visível — MaterialButton vs TextView

## Contexto
App Mp3Player Android. 5 botões de filtro no topo da aba "Músicas": Todas, Favoritas, A-Z, Lista, Sel. O texto não aparecia — os botões ficavam verdes uniformes sem nenhum texto visível.

## O que deu errado

### 1. Mudança de tema AppCompat â†’ MaterialComponents quebrou os botões
- `TagEditorActivity` usava `TextInputLayout` do Material Components, que REQUER tema `MaterialComponents`
- Ao 

---
tipo: aprendizado
tags: [vis-network, pseudo-3d, profundidade, eixo-z, esfera-de-conhecimento, cerebro-vivo, grafo]
data: 2026-08-04
contexto: Pedido para incluir efeito 3D (e 4D) no grafo do conhecimento. Avaliado que vis-graph3d/WebGL reescreveriam todo o motor de fisica/labels/zoom. Decidido por pseudo-3D no motor 2D atual.
decisao: Simular eixo Z dentro do vis-network 2D. Cada no recebe profundidade inicial por centralidade (hubs na frente ~0.92, folhas ao fundo; + jitter estavel via has

﻿# 2026-07-28: Botões de filtro sem texto visível — MaterialButton vs TextView

## Contexto
App Mp3Player Android. 5 botões de filtro no topo da aba "Músicas": Todas, Favoritas, A-Z, Lista, Sel. O texto não aparecia — os botões ficavam verdes uniformes sem nenhum texto visível.

## O que deu errado

### 1. Mudança de tema AppCompat â†’ MaterialComponents quebrou os botões
- `TagEditorActivity` usava `TextInputLayout` do Material Components, que REQUER tema `MaterialComponents`
- Ao 
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]