---
tipo: aprendizado
tags: [vis-network, malha-viva, traveling-wave, profundidade, pseud-3d, giro, canvas, persistencia-clique]
data: 2026-08-04
contexto: Usuario pediu para o grafo "girar sozinho em 3d de forma viva e natural" e reclamou que os efeitos ao clicar em um no sumiram. Tambem pediu que eu aprenda continuamente a evoluir esses efeitos de malha viva.
decisao: (1) Giro via transform CSS no canvas (rotateZ/rotateX) e ARTIFICIAL: gira o rendering 2D inteiro como folha de papel, sem profundidade real entre nos. MELHOR: camuflar o 3D na PROFUNDIDADE (_zVivo) com uma ONDA VIAJANTE. Ponto-chave: a onda progride com o ANGULO do no em torno do centro -> num lado os nos emergem (ficam grandes/opacos/brilhantes) e no outro submergem (pequenos/translucidos/apagados), lendo como um globo girando. Sentido e velocidade da onda randomizados periodicamente. (2) BUG de clique: o evento 'tick' do vis-network dispara a cada frame e, se o handler fizer nodes.update() regravando opacity/size/sombra de TODOS os nos de forma achatada, qualquer destaque/foco se apaga instantaneamente. FIX: flag bool _destacado setada true nos handlers de foco/clique (focarVizinhanca, destacar) e o tick retorna cedo quando ela esta ativa; limpar()/Home resetam para false.
impacto: Movimento de "giro" tsucu natural e organico (esfera de conhecimento) sem WebGL, custo baixo (posicoes cacheadas a cada 600ms). Efeitos de clique/foco (categoria, cluster, vizinhanca) voltaram a persistir na tela. Performance preservada: _zVivo usa _cachePos mas complemento cum custo O(1) por no. JS validado node --check.
---

# 2026-08-04: Malha viva — onda viajante de profundidade (giro 3D natural) + fix clique

## O que NAO funciona: girar o canvas 2D
- `network` do vis-network é 2D. Aplicar `transform: rotateZ/rotateX` no `canvas` apenas
  gira a imagem renderizada — parece folha de papel girando, artificial, sem profundidade.
- Não dá sensação de "malha viva" e ainda desalinha o hit-test do mouse.

## Tecnica correta: camuflar 3D na profundidade (_zVivo)
- O pseudo-3D já controla `size`, `opacity`, `shadow` por nó conforme `z`.
- Ao fazer a profundidade **viajar** com o ângulo do nó em torno do centro,
  os nós alternam "frente/trás" continuamente: 
  `viajante = sin(0.00030 * _waveVel * t + angulo + raio*3) * 0.16 * _waveDir`.
- Num lado a frente (grandes/brilhantes), no lado oposto o fundo (pequenos/translúcidos) →
  sensação de globo girando. Muito mais vivo que girar o quadro.
- Sentido (`_waveDir`) e velocidade (`_waveVel`) randomizados periodicamente (5-9s).

## Custo: cache de posições
- `network.getPositions()` é O(n). Chamado 1x a cada 600ms via setInterval para
  `_cachePos` + `_cacheCentro` (média). `_zVivo` lê O(1) por nó.
- Alternativa sem cache custaria O(n) por tick a 336 nós → lento. Sempre cachear posições
  quando precoisar de ângulo/raio em loop contínuo.

## Fix do bug: tick sobrescrevia os destaques
- Sintoma: clicar num nó/categoria → o efeito de realce sumia em frações de segundo.
- Causa: handler de `network.on('tick')` reescreve opacity/size/sombra de TODOS os nós
  a cada frame; como dispara depois do clique, apaga a mudança visual do destaque.
- Solução: flag `_destacado`. `focarVizinhanca()` e `destacar()` setam `true`; o tick
  retorna cedo quando `_destacado` é true (congela a decoração viva preservando o foco);
  `limpar()`/`telaInicial()` resetam para `false` (volta o cérebro vivo).

## Pendência / evolução futura (cadeia de aprendizado)
- Se quiser profundidade REAL (parallax por camada) sem WebGL: dar valores de `level`
  por nó e animar leve deriva lateral dos nós de fundo (mais lenta) vs frente (mais rápida)
  ao mover o mouse — imita parallax. Isso seria a evolução natural do "malha viva".
- Direção de escala: `three-fglow`/`3d-force-graph` são a reescrita webgl (pesada p/ celular).
