# Física e Animação Viva do Grafo — Deriva Orbital + Zoom Suave (2026-08-05)

## Contexto
O usuário sugeriu aprimoramentos de Force-Directed Graph: animação por
simulação física, reorganização suave, zoom/pan fluido e renderização WebGL.
Avaliação: o widget (vis-network, 339 nós) já tinha force-directed + física
turbinada + pseudo-3D (profundidade) + zoom/pan. WebGL é otimização prematura
para 339 nós; priorizamos física/anim ação perceptíveis.

## Decisão (aplicada em `scripts/generate-graph-html.py`)
1. **DERIVA ORBITAL REAL** (nova): cada nó orbita o centro num elipse lenta
   com semi-eixos (4..9 / 3..8 px), velocidade angular, fase, excentricidade e
   inclinação próprios e estáveis por id (`_hashId`). Aplicada no `tick` via
   `x: n.x + orb.dx, y: n.y + orb.dy` no `nodes.update`. Amplitude pequena para
   não desmanchar a estrutura; as forças Barnes-Hut continuam dominando.
2. **Zoom mais suave**: `zoomSpeed: 0.35` (era 0.6) + `smoothWheel: true`.
3. **Reorganização em cascata ao arrastar**: em `dragEnd`, os vizinhos do nó
   solto recebem um leve empurrão (`Math.sin/cos` * pulso * 3px) e a física
   é brevemente acelerada (grav -760 / spring 0.05 / damping 0.78) por 450ms,
   voltando à respiração normal — a rede "se reorganiza suavemente" ao mover.

## Técnica/lição importante
O JS vive num f-string Python (template `{{ }}`). Objetos JS `{}` e blocos
`{` DEVEM ser dobrados (`{{ }}`, `{{`), senão o Python levanta
`SyntaxError: f-string: valid expression required`. A regra vale para QUALQUER
bloco JS novo (foram 3 correções: `const _orb = {};`, `forEach(n => {`, e um
`return { dx.. }`).

## Resultado
- Grafo regenerado (339 nós, 1535 arestas), JS validado com esprima (bloco
  484843 chars OK), widget rebuilt + reiniciado (PID 880). Sem erros novos.
- Efeito: nós flutuam em órbitas suaves sobrepostas (movimento perpetuo mais
  rico que a onda de profundidade isolada), zoom mais fluido, arrastar um nó
  desencadeia cascata de reorganização.

## Pendências (não aplicadas)
- WebGL (sigma.js/@antv G6): só vale para milhares de nós (>2k). Manter
  vis-network enquanto o vault for ~centenas de notas.
- Persistir preferências de física do usuário (além de `velGrafo`).

## Conexoes

- [[cluster-hub-programacao]]