---
tipo: aprendizado
tags: [widget, labels, etiquetas, menus, localStorage, persistencia, pywebview, vis-network]
data: 2026-08-04
contexto: Usuario pediu: (1) etiquetas (labels) DESATIVADAS por padrao, ativadas pelo botao 'T'; (2) ocultar os menus (barra de legendas + painel lateral) com um clique persistindo a escolha.
decisao: (1) Inverter semantica de labelsOcultos: oculto e o PADRAO. Regra: oculto = localStorage.getItem('labelsOcultos') !== 'false'. Ou seja: ausente, 'true' ou qualquer outro valor => etiquetas ocultas (font.size 0); apenas 'false' explicito => mostra (font.size 11). O botao 'T' grava 'false' (mostra) ao ativar. (2) Botao flutuante 'menu' (mk-menu-btn) alterna a visibilidade do #header e #painel lateral, persiste em localStorage.menuOculto, expande #net para height 100vh quando oculto e chama network.redraw().
impacto: Widget abre limpo, sem etiquetas, sem menus; usuario personaliza com 1 clique; escolha sobrevive reload/regeneracao via pywebview. Validado node --check e preflight 100% PASS. Memory #85.
---

# 2026-08-04: Labels ocultas por padrão + botão de ocultar menus persistente

## 1. Etiquetas ocultas por padrão
- Novo padrão: oculto = `localStorage.getItem('labelsOcultos') !== 'false'`.
  - ausente / 'true' / outro -> font.size 0 (ocultas)
  - 'false' explícito -> font.size 11 (visíveis)
- Locais corrigidos (todos usam a MESMA regra):
  - `aplicarLabels()` no WIDGET_JS_EXTRA (linha ~420)
  - `ctrl.onmousedown` do botão 'T' (linha ~428) — ATIVAR = mostrar
  - `_ajustarFontes()` no generate-graph-html.py
  - `restore_initial_state` e `update_labels_on_reload` (widget)
- `toggle_labels` (via pyside API) já alterna por font.size atual e persiste
  `size===0 ? 'true' : 'false'` — consistente com o novo padrão.

## 2. Ocultar menus com clique (header + painel lateral)
- Botao flutuante `mk-menu-btn` (canto superior direito, `\u2630`).
- Alterna `#header` (barra de legendas/categorias/clusters) e `#painel` lateral.
- Persiste em `localStorage.menuOculto === 'true'`.
- Expande `#net` para `height:100vh` quando oculto e chama `network.redraw()`.
- Ícone/opacidade mudam para indicar estado (oculto=transparente).

## Boas práticas lembradas
- Sempre validar: `py_compile`, `node --check` (no JS extra sem tag `<script>`),
  `preflight_check.py` (cláusula pétrea).
- NÃO confiar na 1ª edição: conferir que TODAS as leituras da mesma chave usam a
  mesma regra (havia linhas antigas `=== 'true'` residuais em 420/428).