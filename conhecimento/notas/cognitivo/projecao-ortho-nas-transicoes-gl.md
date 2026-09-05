---
tags: [1204, 575px, centro, cognitivo, general, util]
aliases: [Projecao ortho nas transicoes GL]
date: 2026-08-20
---

# Projecao ortho nas transicoes GL

**Dominio:** general

## Problema
A pagina capturada tem a mesma proporcao da tela (1080x2400, aspect 0.45).
Com frustumM(-aspect, aspect, -1, 1, 2, 8) + translate z=-3.5, o quad -1..1
aparecia com ~57% do tamanho, deixando bordas pretas laterais (distorcao vertical).

## Correcao
Usar projecao ortografica orthoM(-1, 1, -1, 1, 2, 8). Como a textura tem a
mesma proporcao da tela, o quad [-1,1]x[-1,1] preenche a tela inteira sem
faixas. O shader ja faz a perspectiva manual para o cubo (perspective =
2.0/(2.5 + nx*sinA)), entao ortho e suficiente.

## Validacao no dispositivo
screenrecord + analise de frames (video 720x1280 com letterbox, largura util 575px):
- Esfera: contentW=575 sempre, curvatura visivel (altura 1178 bordas vs 1204 centro)
- Malha 3D: contentW=575, ondas visiveis, escurece no pico
- Cubo 3D: contentW encolhe 413 -> 140 conforme o cubo gira em perspectiva
- Girar (Canvas): contentW encolhe 575 -> 146, pagina gira para longe
- Todos terminam na LibraryActivity sem crash

## Licao
Quando a tex
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]