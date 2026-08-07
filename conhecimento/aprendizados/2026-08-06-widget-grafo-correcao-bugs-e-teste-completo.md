---
tipo: erro
tags: [grafo, widget, pywebview, bug, teste, harness, node, vis-network, tdz]
data: 2026-08-06
contexto: Varredura + correção um-a-um de todos os bugs do widget grafo desktop (Cerebro Vivo), seguida de teste completo via harness headless Node.
decisao: Corrigir 8 bugs e validar com harness Node que executa os blocos JS reais do HTML gerado (stubs de DOM/vis/localStorage/bridge), mais subprocesso do widget real.
impacto: Painel de controles voltou a funcionar (tema, velocidade, orbita, busca, tamanho, T/M), arraste/resize via RESIZE_JS reativados, reload em tempo real via API_INJECT reativado, grafo principal sem crash no boot.
---

# Widget Grafo Desktop — Correção de Bugs + Teste Completo (2026-08-06)

## Bugs corrigidos (um a um)

1. **CRÍTICO — Chaves duplas `{{ }}` no seletor de tema** (`scripts/widget_grafo.py`)
   - O bloco `WIDGET_JS_EXTRA` (string plana) tinha `{{ nome: 'Neon' }}` (resíduo de
     template f-string copiado de `generate-graph-html.py`). Como o bloco é injetado
     verbatim via `_build_view()`, o `{{` vazava literal para `docs/grafo_widget.html`
     → SyntaxError JS ("Unexpected token {") → IIFE inteiro do painel morria.
   - Correção: `{{` → `{` (6 ocorrências). Introduzido no commit `cf07da08`.

2. **CRÍTICO — Widget rodando com HTML quebrado** — após corrigir a fonte, rebuildar
   via `_build_view()` (regenera `docs/grafo_widget.html`) e reiniciar o processo.

3. **MÉDIO — `RESIZE_JS` nunca injetado** — `_build_view()` só injetava `WIDGET_JS`,
   `WIDGET_CSS` e `WIDGET_JS_EXTRA`. `RESIZE_JS` (cria `#mk-drag`/`#mk-resize`) era
   código morto → arrastar a janela não funcionava (`mover(` = 0 no HTML).
   Correção: injetar `RESIZE_JS` antes de `</body>`.

4. **MÉDIO — `API_INJECT` nunca injetado** — reload em tempo real (poll de versão →
   `regenerar()`) estava morto. Correção: injetar com `%POLL_MS%` substituído.

5. **BAIXO — `test_widget_live.py` quebrado** — `btnBug`/`btnFechar` trocados,
   sintaxe inválida (`typeof _destacado !== 'undefined' 0 ?`), `indexOf('Neon') !== 0`.
   Correção: variáveis corretas + sintaxe + `> -1`. Também: `webview.start()` num
   harness GUI trava em thread; para automação headless usar VM Node (ver abaixo).

6. **BAIXO — `generate-graph-html.py --help` quebra** — `--help` era tratado como
   caminho de output → FileNotFoundError. Correção: cláusula `-h/--help` → print doc.

7. **MÉDIO — Botão 'T' alternava painel em vez de etiquetas** — `ctrl.onmousedown`
   era "toggle painel"; doc de 08-04 dizia "toggle labels". Correção: alterna
   `labelsOcultos` (`false` mostra) + `aplicarLabels()`. `toggle_labels is not a
   function` era histórico (API PySide removida), não existe mais no código.

8. **ALTO — TDZ no template principal (`original`)** — `_clusterCorPorCl` usa
   `original[n.id]` (linha ~1003) ANTES do `const original = {}` (linha ~1270) →
   "Cannot access 'original' before initialization" → script principal crashava no
   boot (também em navegador). Correção: mover inicialização de `original`/
   `arestaOriginal` para logo após `const network`. Introduzido em `92732ab3`.

9. **ALTO — Typo `_aplicarForcesTema`** — `aplicarTema()` chamava
   `_aplicarForcesTema` (com E) mas a função é `_aplicarForcasTema` (com A);
   ReferenceError engolido pelo `catch(e){}` → tema nunca persistia.
   Correção: chamada → `_aplicarForcasTema`.

## Teste

- **py_compile** em todos os scripts alterados: OK.
- **esprima** nos 4 blocos JS do `widget_grafo.py` e nos 7 `<script>` do
  `docs/grafo_widget.html`: todos OK.
- **Harness headless Node** (`harness.js`): executa os blocos JS reais do HTML com
  stubs de `vis.DataSet/Network`, DOM, `localStorage`, `window.pywebview.api`.
  Resultado: **40/40 PASS** — funções globais, 21 botões `.lg` (cat/cl/st/dom/home/
  all), painel `#mk-controles`, 2 selects (tema+tamanho), 2 sliders (vel+orb),
  busca, botões T/M, RESIZE_JS (`#mk-drag`/`#mk-resize`), API_INJECT, e interações:
  tema→persiste, slider vel→persiste, slider orb→bridge, busca→destacar(txt),
  tamanho→bridge redimensionar, T→labelsOcultos, M→menuOculto.
- **Widget real**: iniciado via `pythonw` em background, permaneceu vivo (PID 6316),
  sem erros no `docs/widget_log.txt`, geometria salva na sessão atual.

## Lições

- **Validar com esprima NÃO detecta erro de runtime (TDZ, ReferenceError)**.
  Esse é o padrão que falhou nos dias 04-05 (validava sintaxe mas não executava).
  Para JS injetado, usar harness Node com stubs que executa de verdade.
- Ao copiar JS com `{{ }}` entre arquivos (f-string vs string plana), conferir se o
  alvo usa f-string; senão as chaves duplas viram literal.
- `catch(e){}` vazio em `aplicarTema` escondeu o typo por dias — logs de erro JS
  (early_error/API_INJECT) ajudam mas só via `debug_log` no widget.
- Botões com `title` prometem comportamento; testar a ação real (onmousedown/click).
- Preflight falhou em "Constituição deployada divergente" — pré-existente, não
  relacionado a este trabalho (nenhum `config/agents/*.md` alterado).

## Conexoes

- [[maxiterations-hard-stop-forca-parada-prematura-mesmo-sem-obj]]