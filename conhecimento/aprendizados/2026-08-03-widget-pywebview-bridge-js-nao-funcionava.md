---
tipo: erro
tags: [widget, pywebview, edgechromium, bridge, js-api, file-url, http-server]
data: 2026-08-03
contexto: Widget "Cerebro Vivo" (pywebview 6.2.1, edgechromium) nao disparava o bridge JS->Python: versao() nunca era chamada, geo nunca salvava, `loaded` nunca disparava.
---

# Widget pywebview edgechromium: bridge JS nunca funcionava

## Causa raiz (DUPLA)

1. **Atributo publico nao-callable no js_api**: `Bridge` tinha `self.win = win` (publico).
   O pywebview, ao expor o js_api (`webview/util.py` -> `get_functions()`), itera `dir(js_api)`
   e serializa RECURSIVAMENTE todo atributo publico nao-callable. O objeto Window exposto
   via `self.win` fazia `getattr(win, ...)` disparar erros COM "can only be accessed from the
   UI thread" + `maximum recursion depth exceeded` (spam "Error while processing win.native...").
   A excecao era capturada no `except` de `generate_js_object()` e o `finish_script` (que
   configura `window.pywebview.api` e dispara o pywebviewready JS) NUNCA era injetado.

2. **URL via `resolve()` usa HTTP server**: passar `url=str(Path.resolve())` faz o pywebview
   iniciar um Bottle HTTP server (`http://127.0.0.1:porta/...`). Nesse modo, o evento
   `loaded` do pywebview NAO disparava no edgechromium (regressao observada na pratica).
   Com URL `file:///...` explicita, o carregamento e a injecao do bridge funcionam.

## Decisao / Correcao

- `self.win` -> `self._win` (privado). O pywebview pula atributos com `_` e a doc oficial
  confirma: "Class attributes starting with an underscore are not exposed".
- URL explicita: `url='file:///' + str(view.resolve()).replace('\\', '/')`.

## Verificacao

- Com as duas fixes: `[pywebview] loaded event fired` + `versao()` chamada a cada POLL_MS
  (2s) + `guardar_geo()` persistindo geo + `regenerar()` disparando ao tocar arquivo do vault
  (auto-sync end-to-end comprovado).
- Teste isolado comprovou: mesmo HTML via `file://` -> `loaded` dispara; via HTTP server ->
  `loaded` nao dispara. O HTML NAO era o problema.

## Impacto / Lição

- js_api do pywebview DEVE conter apenas metodos (callables). Nunca atributos publicos que
  apontem para objetos nativos/complexos; usar privados (`_nome`) ou marcar `_serializable = False`.
- Para janelas que carregam arquivo local unico (widget), preferir `file:///` explicito em vez
  de `Path.resolve()` para evitar o HTTP server (e os 404 de recursos relativos).
- `logger.exception` do pywebview so aparece com `PYWEBVIEW_LOG=DEBUG`; usar essa env var
  para diagnosticar bridge.

## Arquivos

- `scripts/widget_grafo.py`: fix aplicada (`_win`, URL file://, bridge funcionando).
