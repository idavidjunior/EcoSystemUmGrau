---
tipo: erro
tags: [opengl, transicoes, biblia, projecao, ortho]
data: 2026-08-19
contexto: Motor de transicoes OpenGL ES 2.0 do app BibliaEstudoCompleta
decisao: Trocar frustumM por orthoM(-1,1,-1,1,2,8) e remover a multiplicacao pos.x *= uOldAspect no shader
impacto: Pagina preenche a tela inteira sem distorcao; 4 efeitos validados no device
---

# Projecao ortho nas transicoes GL

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
Quando a textura e um screenshot da propria tela (mesma proporcao), projecao
ortho resolve o preenchimento. frustum so e necessario se houver deformacao
tridimensional real que exija profundidade de camera; aqui o shader cuida disso.
