---
tipo: padrao
tags: [grafo, widget, vis-network, fisica, tooltip, mcp, conhecimento, controle-velocidade]
data: 2026-08-04
contexto: Widget "Cerebro Vivo" se movia devagar, efeitos discretos, sem controle de velocidade nem tamanho, e sem explicacoes nos botoes/nos.
decisao: Turbinar fisica e efeitos, adicionar slider de velocidade, presets de tamanho de quadro, agrupar botoes de layout com cor distinta, adicionar filtro MCPs/Conhecimento e tooltips descritivos em botoes e nos.
impacto: Grafo mais vivo e configuravel; navegacao do conhecimento ganha contexto descritivo ao passar o mouse.
---

# Widget do grafo turbinado (velocidade + tamanho + tooltips + MCPs/Conhecimento)

## O que foi feito
- **Fisica mais energetica** (`scripts/generate-graph-html.py`, template JS):
  - maxVelocity 6->13, timestep 0.2->0.32, damping 0.88->0.82,
    gravitationalConstant -620->-720, springConstant 0.03->0.045.
  - Efeitos: onda viajante 0.16->0.26, deriva 0.13->0.20, pulso base
    0.05->0.07 e escala 0.4->0.55, spikes 3.2-5.5s -> 1.6-3.2s,
    solo espontaneo 0.006->0.010, refratario 260->240ms.
- **Controle de velocidade**: `_aplicarVelocidade(v)` multiplica ondas/pulsos
  (`_velGlobal`) e reescala a fisica (damping ~ 1/sqrt(v)). Slider 0.25x-3x
  no painel, persistido em `localStorage.velGrafo`.
- **Presets de tamanho do quadro** (`WIDGET_JS_EXTRA`): select Compacto/Media/
  Padrao/Grande/Maxima -> `pywebview.api.redimensionar(w,h)`.
- **Botoes de layout agrupados** com cor destaque `#cba6f7`: etiquetas (T) +
  menus (M) num grupo visual distinto no painel de controles.
- **Filtro de dominio**: botoes `MCPs`/`Conhecimento` (data-filter="dom"),
  classificando por tags contendo 'mcp'; hubs/categorias gerais ficam fora.
- **Tooltips**:
  - Botoes da legenda ganharam `title` descritivo via novos dicts
    `CATEGORIA_DESC`, `CLUSTER_DESC`, `STATUS_DESC` + botoes Home/Limpar/MCPs.
  - Nos: tooltip estruturado `# label / Categoria / Cluster / Status / Tags /
    --- / resumo(400 chars)` em vez de so o excerpt.
  - CSS `.vis-tooltip` (max-width 420px/85vw, max-height 70vh, scroll,
    pre-line) + media query 720px para header/legend/painel responsivos.
- **Centro de referencia do movimento** = centro do quadro visivel
  (`network.getViewPosition()`), nao a media das posicoes dos nos.

## Validacao
- `python -m py_compile` em ambos os scripts: OK.
- esprima: todos os 5 blocos JS do widget validos (bloco principal 480KB).
- `docs/grafo.html` regenerado: 339 nos | 1537 arestas.
- Widget reiniciado (PID 8368); log sem erros novos (so o antigo
  `toggle_labels is not a function`, nao bloqueante).

## Arquivos
- `scripts/generate-graph-html.py` — template HTML/JS + dicts de descricao.
- `scripts/widget_grafo.py` — WIDGET_JS_EXTRA (painel de controles).
- `docs/grafo.html` e `docs/grafo_widget.html` — gerados.

## Aprendizados
- vis-network tooltip usa texto simples (nao HTML): usar `\n` + CSS
  `white-space: pre-line` para bloco legivel.
- Para mover a onda em torno do viewport, `network.getViewPosition()` retorna o
  ponto central visivel — melhor que calcular centroide dos nos.
- LocalStorage persiste preferencias (velocidade, tamanho, labels, menus) sem
  depender do bridge Python.

## Conexoes

- [[2026-08-04-foco-vocal-via-jarvis-voz-orienta-o-grafo-do-conh]]
- [[2026-08-04-tamanho-por-uso-real-iniciar-gui-com-pythonw-impl]]