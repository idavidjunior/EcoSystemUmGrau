---
tipo: aprendizado
tags: [grafo, vis-network, fisica, barnesHut, movimento-organico, cerebro-vivo, sinapses, widget]
data: 2026-08-04
contexto: Usuario pediu refinamento do widget do grafo do conhecimento: movimento organico perpetuo (stabilization:false + barnesHut com timestep lento), respiracao do layout e "pulse" de sinapses (arestas brilham quando o vault atualiza).
decisao: Implementado em scripts/generate-graph-html.py (bloco JS do grafo gerado): physics.stabilization=false + minVelocity:0 + maxVelocity:6 + timestep:0.2 + adaptiveTimestep:false + barnesHut com centralGravity/avoidOverlap. Respiracao do layout via setInterval ~3s oscilando gravitationalConstant/centralGravity/springConstant (ciclo ~22s). Pulse de sinapses aleatorias 1-3 arestas a cada 3.2-5.5s + cascata de ~10% das arestas quando a URL tem 'rc' (marcador que o widget adiciona ao detectar mudanca de versao).
impacto: Grafo nunca congela, "cerebro vivo" respira e as sinapses disparam. Preflight ALL PASS. Ao detectar atualizacao do vault, o widget recarrega com 'rc' na URL e dispara uma onda de sinapses em cascata (sensacao de cognicao viva no momento do aprendizado).
---

## Aprendizados sobre vis-network (validados online)

### 1. improvedLayout so funciona ANTES da criacao da rede
`layout.improvedLayout` usa o algoritmo Kamada-Kawai para o layout INICIAL e so
tem efeito durante a estabilizacao. Chamar `network.setOptions({layout:{improvedLayout:true}})`
depois de criar a rede NAO faz nada. Para redes grandes interconectadas (>100 nos)
ele falha e reverte para o metodo antigo. Com `stabilization:false`, o movimento
organico perpetuo ja espalha os nos naturalmente — nao precisa de improvedLayout.

### 2. Movimento organico perpetuo (nunca travar)
```
physics: {
  solver: 'barnesHut',
  barnesHut: { gravitationalConstant:-620, centralGravity:0.28, springLength:120,
               springConstant:0.03, damping:0.88, avoidOverlap:0.55 },
  minVelocity: 0,     // nunca atinge "estabilizado" -> nao para
  maxVelocity: 6,     // limita velocidade -> movimento lento e suave
  timestep: 0.2,      // passo lento -> mais estavel/organico
  adaptiveTimestep: false,
  stabilization: false
}
```
- `avoidOverlap` (0..1): usa o raio do no para evitar sobreposicao. 1 = maximo.
- `minVelocity:0` impede o modulo tirar conclusao de "estabilizado" e parar.

### 3. Respiracao do layout (ciclo ~22s)
Oscilar suavemente as forcas via setInterval (~3s): "inspira" (mais repulsao,
espaca) e "expira" (mais coesao, aproxima). Usa seno lento (0.78 + 0.22*sin).

### 4. Pulse de sinapses
- Pulso aleatorio: 1-3 arestas acendem (azul nos destinos) a cada 3.2-5.5s.
- Cascata real: quando a URL carrega com `?rc=<timestamp>` dispara uma onda de
  ~10% das arestas uma a uma (intervalo 90ms). O widget ja adiciona `rc` quando
  detecta mudanca de versao (widget_grafo.py checar()).

### 5. Assembly do HTML standalone (vendor embutido)
O vis-network v9.1.9 fica embutido (nao CDN) — o `{{`/`}}` que o regex pega e
do vendor minificado, NAO do nosso JS. Para validar o nosso bloco, limitar a
busca a apos um marcador proprio (ex: 'Respiracao do layout').

## Params-chave do barnesHut (defaults vs nossos)
| param | default | nosso | efeito |
|-------|---------|-------|--------|
| theta | 0.5 | 0.5 | precisao/custo |
| gravitationalConstant | -2000 | -620 | forca de repulsao |
| centralGravity | 0.3 | 0.28 | puxa pro centro |
| springLength | 95 | 120 | comprimento repouso das arestas |
| springConstant | 0.04 | 0.03 | resistencia das molas |
| damping | 0.09 | 0.88 | amortecimento (0..1) |
| avoidOverlap | 0 | 0.55 | evita sobreposicao |
| timestep | 0.5 | 0.2 | passo da simulacao |
| minVelocity | 0.1 | 0 | nunca para |
| maxVelocity | 50 | 6 | velocidade maxima |