---
tipo: aprendizado
tags: [vis-network, pseudo-3d, profundidade, eixo-z, esfera-de-conhecimento, cerebro-vivo, grafo]
data: 2026-08-04
contexto: Pedido para incluir efeito 3D (e 4D) no grafo do conhecimento. Avaliado que vis-graph3d/WebGL reescreveriam todo o motor de fisica/labels/zoom. Decidido por pseudo-3D no motor 2D atual.
decisao: Simular eixo Z dentro do vis-network 2D. Cada no recebe profundidade inicial por centralidade (hubs na frente ~0.92, folhas ao fundo; + jitter estavel via hash do id) e DEPOIS flutua no tempo (_zVivo = base + duas senoides de periodos diferentes por no). Tamanho (esc=0.74+0.5*z), opacidade (0.55+0.45*z) e glow (shadowSize ~ z) refletem z. Arestas modulam opacidade pela profundidade media das pontas (zM). A 4a dimensao: espacial (profundidade) agora soma-se a temporal (pulsos/cascata) ja existente.
impacto: Efeito relevo/esfera de conhecimento com movimento organico autonomo, sem dependencia WebGL, preserva fisica/clusters/labels/microscopio. Funciona no celular. JS validado via node --check. Rebuild view OK. Memory #80.
---

# 2026-08-04: Pseudo-3D vivo — profundidade sem WebGL

## Por que pseudo-3D e nao 3D real
- `vis-graph3d` nao faz fisica de forca nem movimento organico dos nossos nos (e estatico/por tempo).
- `three-fglow`/`3d-force-graph` exigem WebGL, reescrevem o motor e pesam no celular.
- Logo: ilusao de profundidade no motor 2D preserva fisica, clusters, labels e microscopio.

## Implementacao (scripts/generate-graph-html.py)
1. `_hashId(id)` — hash estavel de string/number para fase e jitter.
2. `_zInicial(n)` — profundidade base: `0.25 + 0.6*min(1,size/40)` (size ~ grau => centralidade); hubs = 0.92; + jitter ±0.11.
3. `_zBase`/`_zFase` — profundidade inicial e fase unica por no.
4. `_zVivo(id, t)` — `base + 0.16 * (sin(t*0.0007+f) + sin(t*0.00042+f*2.3)) * 0.5`, clamp 0.04..1. Flutua autonomo.
5. No tick, por no: `esc=0.74+0.5*z`, `op=min(1, base*(0.55+0.45*z))`, `shadow: z>0.3`, `shadowSize ~z`; tamanho = original * esc (* pulso se fase). 
6. Arestas: `opacity = 0.25 * (0.55 + 0.9*(zA+zB)/2)`.

## 4a dimensao
- Temporal (ja existia): pulsos de sinapse aleatorios + cascata no `rc`.
- Espacial (nova): relevo em profundidade (eixo Z simulado). Juntas dao a sensacao de "esfera viva".

## Validacao
- `py_compile` OK; `node --check` sobre o JS do grafo OK; marcadores `_zVivo`/`_zBase`/`_zFase`/`pseudo-3D`/`zM` presentes no HTML; `_build_view()` OK.