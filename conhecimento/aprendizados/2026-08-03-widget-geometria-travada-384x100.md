---
tipo: erro
tags: [widget, pywebview, geometria, vis-network, responsivo, grafo]
data: 2026-08-03
---

# Widget "Cerebro Vivo" — geometria travada em 384x100 e detalhe do container vis.js

## Contexto

O widget desktop `scripts/widget_grafo.py` (janela pywebview mostrando o grafo do
conhecimento em `docs/grafo_widget.html`) abria **invisível / do tamanho mínimo**
(geo `width:384, height:100`). O usuário relatou "não consigo ver nada, o tamanho
do widget não ficou responsivo".

## Causa raiz

Ciclo vicioso de geometria corrompida:

1. O arquivo `docs/grafo_widget_geometria.json` ficou gravado como `384x100`
   (valor degenerado, provavelmente de um `report()` prematuro/errado durante
   sessões de debug anteriores).
2. Ao abrir, `create_window()` usava `width=384, height=100` → janela micro.
3. O JS `report()` roda em `pywebviewready` e `resize` e chamava
   `guardar_geo(innerWidth, innerHeight)` → **re-salvava 384x100** de novo.
4. Resultado: o tamanho pequeno ficava eternizado — a janela nunca crescia.

Não havia nenhum guard contra geometrias degeneradas.

## Observações complementares

- Com `_win` privado (fix da sessão anterior do bridge), o **HTTP server
  (`url=str(view.resolve())`) voltou a funcionar**: log mostra
  `GET /vendor/vis-network.min.js 200` → o grafo renderiza. HTTP server carrega
  os recursos relativos que `file://` bloqueia silenciosamente no WebView2.
- O container do grafo vis.js é `id="net"` (e **não** `#mynetwork`). Procurar
  `#mynetwork` no HTML gera falso negativo. O `#net` tem
  `height:100vh !important; width:100vw !important`.

## Decisão / correção

Adicionar clamp de geometria em `scripts/widget_grafo.py`:

- `MIN_W, MIN_H = 400, 300`.
- `_carregar_geo()`: se `width < MIN_W` ou `height < MIN_H`, rejeita o valor
  corrompido e usa `DEFAULT_W, DEFAULT_H (1280, 800)` (preservando x/y).
- `guardar_geo()`: **ignora** geometry onde `w < MIN_W` ou `h < MIN_H`, para
  nunca gravar de novo tamanhos degenerados.

## Impacto

- Widget abre em ~1264x749 (visível, responsivo) em vez de 384x100.
- Geometria válida é salva/persistida normalmente; degeneradas são descartadas.
- Regra geral: geometrias de janelas persistidas devem ser clamped no load E no
  save — nunca confiar que basta "resetar o arquivo".

## Próximos passos

- Confirmar visualmente o grafo viva no widget.
- (Opcional) cláusula pétrea de preflight passou antes do commit.
