# Painel de Controles do Grafo — Posicionamento Seguro (2026-08-05)

## Contexto
O painel `#mk-controles` (velocidade, tamanho, etiquetas/menus) sobrepunha os botões de controle da legenda (`#header`) porque o `WIDGET_CSS` não era injetado no HTML final — o header ficava sempre visível no topo e o painel fixo em `top:22px` cobria a legenda.

## Causa raiz (importante)
`WIDGET_CSS`, `RESIZE_JS` e `API_INJECT` em `scripts/widget_grafo.py` eram **código morto**: `_build_view()` só injetava `WIDGET_JS` + `WIDGET_JS_EXTRA`. Qualquer regra CSS adicionada nesses blocos nunca chegava ao HTML. Confirmado por busca em `docs/grafo_widget.html` (ausência de `mk-drag`, `header { opacity:0`, `media query`).

## Solução aplicada
1. **Painel posicionado dinamicamente**: `reposicionarPainel()` mede `header.getBoundingClientRect()` e posiciona o painel logo abaixo do header (`r.bottom + 10px`), ou em `top:22px` quando o header está oculto (altura 0). Conectado a `resize`, `DOMContentLoaded`, `pywebviewready` e `contextmenu` (clique direito alterna o header).
2. **`aplicarMenus()`** agora chama `reposicionarPainel()` após ocultar/exibir o header (delay 60ms).
3. **Injeção do CSS corrigida**: `_build_view()` agora também injeta `<style>` com `WIDGET_CSS` antes de `</head>`. Isso faz o header ocultar por padrão (`opacity:0; height:0`) e revelar com clique direito (`body.desktop`), além de aplicar a media query responsiva de 720px.
4. Removida a regra fixa `body.desktop #mk-controles { top:190px }` (frágil) em favor do cálculo dinâmico.

## Resultado
- Widget rebuildado (`docs/grafo_widget.html`, 1195974 bytes).
- Validação: `py_compile` OK; JS validado com esprima nos 5 blocos (vendor parcial OK, bloco 3 = 480593 chars OK, WIDGET_JS_EXTRA = 11508 chars OK).
- CSS presente no HTML: `#header { transition: opacity .25s ease; opacity: 0...`, `@media (max-width: 720px)`, `mk-drag`.
- Widget reiniciado (PID 9596) via `pythonw scripts/widget_grafo.py`. Sem erros novos no log; `toggle_labels is not a function` é pré-existente e não bloqueante.

## Lição
Ao adicionar CSS a `scripts/widget_grafo.py`, SEMPRE rebuildar via `_build_view()` e conferir que a regra aparece em `docs/grafo_widget.html` (grep). Blocos `WIDGET_CSS`/`RESIZE_JS`/`API_INJECT` não são injetados por si só.

## Conexoes

- [[cluster-hub-programacao]]