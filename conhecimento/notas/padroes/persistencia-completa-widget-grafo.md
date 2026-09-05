---
tags: [extra, fit, nao, opencode, padrao, sobrescrever]
aliases: [persistencia completa widget grafo]
date: 2026-08-10
---

# persistencia completa widget grafo

**Fonte:** opencode

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
- Restore de boot em setTimeout(2600): reaplica filtro (busca o botao `.lg` pelo data-filter/data-value para pegar a cor) e
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]