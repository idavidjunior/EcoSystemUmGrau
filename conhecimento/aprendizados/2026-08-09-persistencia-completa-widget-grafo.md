---
tipo: padrao
tags: [persistencia, widget, grafo, localStorage, camera, filtro]
data: 2026-08-09
contexto: Usuario exigiu que todas as escolhas de personalizacao do widget "Cerebro Vivo" persistam entre execucoes.
decisao: Persistir tema, velocidade, orbita, etiquetas, painel, camera (zoom/pane) e filtro/destaque ativo.
impacto: Widget restaura a visao e o destaque exatos do usuario a cada boot, regeneracao (?rc=) e reinicio do PC.
---

## Decisao

Toda personalizacao do widget do grafo persiste em localStorage:
- `temaGrafo`, `velGrafo`, `orbGrafo`, `labelsOcultos`, `painelGrafoVisivel` (ja existiam no widget-extra.js)
- `modo3D`, `waveIntensidade`, `flashEnabled` (lado do grafo, gerado por generate-graph-html.py)
- **NOVOS**: `camGrafo` (camera: x, y, scale) e `destGrafo` (filtro ativo: {f, v})

## Implementacao (generate-graph-html.py)

- `_salvarCamera()` grava view position + scale; disparada por `network.on('zoom')`, `('dragEnd')`, `('animationFinished')` e `beforeunload`.
- `_restaurarCamera()` aplica via `network.moveTo({position, scale, animation:false})`, clamp scale 0.05..6.
- `destacar(filtro, valor, corGrupo, semFit)`: parametro novo `semFit` evita fit no restore de boot para nao sobrescrever a camera salva.
- `limpar()` remove `destGrafo`; `telaInicial()` salva camera apos o moveTo.
- Restore de boot em setTimeout(2600): reaplica filtro (busca o botao `.lg` pelo data-filter/data-value para pegar a cor) e depois restaura camera — depois do fit inicial (1200ms + ~1s de animacao).
- `guardaInicial` movido de 2500 para 3400ms para capturar como "home" a visao ja restaurada.

## widget-extra.js

- `resetWidgetState` (botao ↺) agora remove `camGrafo` e `destGrafo` junto com o resto.

## Licoes

- vis-network: `moveTo`/`fit`/`focus` NAO disparam 'zoom'/'dragEnd' (sao so do usuario); usar 'animationFinished' para animacoes programaticas.
- Restore de camera/filtro DEVE rodar apos o fit inicial, senao o enquadramento sobrescreve a visao salva.
