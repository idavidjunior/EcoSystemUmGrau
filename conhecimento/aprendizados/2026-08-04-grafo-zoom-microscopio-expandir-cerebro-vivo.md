---
tipo: aprendizado
tags: [vis-network, zoom, microsocpio, clustering, physics, barnesHut, grafo, widget, labels]
data: 2026-08-04
contexto: Refinamento do widget "Cerebro Vivo" (scripts/widget_grafo.py + scripts/generate-graph-html.py) para movimento mais vivo/realista e zoom com papel narrativo.
decisao: Movimento organico = physics.stabilization:false + timestep:0.2 + maxVelocity:6 + minVelocity:0 + adaptiveTimestep:false + barnesHut(avoidOverlap:0.55, damping:0.88). Respiracao do layout via setInterval (~3s) oscilando gravitationalConstant/centralGravity/springConstant (~22s). Zoom: microsocpio mantem fonte legivel (font.size = 13/scale) + expandir via clustering por folhas (zoom-out cluster, zoom-in openCluster). Labels: bug de classe Bridge duplicada corrigido + toggle client-side persistido no localStorage. Cascata de sinapses ao detectar 'rc' na URL.
impacto: Grafo nunca congela, respira e tem cognicao viva. Zoom recuar/agrandar passa a ter funcao narrativa (ver o todo / ver o detalhe). Labels ocultas/visiveis persistem entre reloads. JS validado via node --check. Preflight 100% PASS. Memory #79.
---

# 2026-08-04: Refinamento do grafo — zoom microscópio, expandir e cognição viva

## Decisões técnicas validadas (online)

### vis-network physics (barnesHut)
- `stabilization: false` + `timestep: 0.2` + `maxVelocity: 6` + `minVelocity: 0` + `adaptiveTimestep: false` → movimento perpétuo e lento (nunca "congela").
- `barnesHut.avoidOverlap: 0.55` usa o raio do nó para evitar sobreposição (vis.js docs).
- `damping: 0.88` → balanço suave/amortecido.
- `improvedLayout` só funciona se passado **antes** de `new vis.Network()`, e pode falhar em grafos densos (>100 nós interconectados); com stabilization:false deixamos o balanço orgânico espalhar.

### Zoom microscópio (fonte legível ao ampliar)
- vis.js NÃO tem opção "fix label size" pronta. A compensação validada na comunidade:
  `font.size = base / scale` (aplica no evento `network.on('zoom')`).
- Implementado: `font.size = 13 / scale` (clamp 0.4 ≤ scale ≤ 22).

### Expandir (clustering por zoom)
- vis.js possui `network.cluster({joinCondition, clusterNode})` e `network.openCluster(id)`.
- Estratégia: em zoom-out, agrupa folhas (grau ≤ 1) adjacentes a um mesmo nó; em zoom-in, abre clusters (`openCluster`). Efeito microscópio: recuar = ver o todo, aproximar = ver o detalhe.
- Fonte: exemplo oficial `examples/network/other/clusteringByZoom.html`.

## Bug corrigido (labels que não funcionavam)
- Havia **duas classes `Bridge`** em widget_grafo.py; a segunda (sem `toggle_labels`/`limpar_labels`/`update_labels_on_reload`) sobrescrevia a primeira → botão 'T' chamava método inexistente → não abria.
- Corrigido: classe única + **toggle totalmente client-side** no `localStorage` (`labelsOcultos`), persistindo a escolha do usuário entre reloads (aplicado em `pywebviewready` + `DOMContentLoaded`).

## Efeitos "cérebro vivo" implementados
- Heartbeat (tick): respiração de opacidade (~4s) + pulso individual de tamanho/glow por nó (fase única, throttle ~3x/s para não matar perf em 336 nós).
- Pulsos de sinapse: 1–3 arestas aleatórias a cada 3.2–5.5s.
- **Cascata de sinapses** ao detectar `rc` na URL (dispara ~10% das arestas uma-a-uma quando o vault atualizou).

## Validação
- `python -m py_compile` (ambos os .py): OK
- `python scripts/generate-graph-html.py` → 336 nós, 1502 arestas
- `node --check` sobre o JS gerado: OK (sem syntax error)
- `python -c "import widget_grafo; w._build_view()"` → view OK (vis-network embutido, sem chaves `{{ }}` residuais no nosso código)
- `python scripts/preflight_check.py` → **TODOS TESTES PASSARAM**

## Como testar visualmente
- Abra `docs/grafo.html` no navegador → veja o balanço + respiração + pulso de sinapses.
- Abra o widget (`python scripts/widget_grafo.py`) → clique 'T' para ocultar labels → feche e reabra → labels permanecem ocultas.
- No widget, modifique alguma nota em `conhecimento/notas/` → trigger de versão → recarrega com `rc` → cascata de sinapses dispara.