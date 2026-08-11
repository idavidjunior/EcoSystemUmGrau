# Widget Grafo: Busca, Stats Vivos e Controle de Orbita (2026-08-05)

## Contexto
Três sugestões de evolução do widget do grafo: (1) persistir preferências
além de velocidade/tamanho, (2) busca/destaque por palavra no grafo,
(3) stats vivos com contagem por cluster.

## Implementação
1. **Slider de Órbita (`orbGrafo`)** — controla a amplitude da deriva orbital
   (0..3x), persistido em localStorage e aplicado via `_aplicarOrbita(fator)`
   que reescala `_orbAmplGlobal` dentro de `_derivaOrbital` no gerador.
   Adicionado ao painel `#mk-controles` (`scripts/widget_grafo.py`).
2. **Busca por palavra** — campo `Buscar no grafo...` no painel; a cada tecla
   chama `destacar('txt', termo, cor)`. Novo filtro `txt` em `destacar`
   (`generate-graph-html.py`) que procura o termo (case-insensitive) no
   `label`, `title` (resumo), `slug` e `tags` de cada nó; campo vazio chama
   `limpar()`.
3. **Stats vivos** — `_atualizarStats()` no gerador reescreve `#stats` com
   `total nos | conexões • cluster:n ...` (por cluster, ordenado), atualizado
   a cada 3s + após load. Reflete estado atual sem recarregar a página.

## Detalhes técnicos
- `_aplicarOrbita` e `_atualizarStats` são expostos no escopo global do bloco
  JS principal; o WIDGET_JS_EXTRA (painel) os chama via `typeof` guard.
- `aplicarPersistidos()` no widget agora restaura velocidade + órbita + stats.
- Validação: py_compile OK; esprima OK nos 5 blocos do widget (bloco 3 =
  487487 chars, bloco 4 = 14189 chars). Widget rebuildado e reiniciado
  (PID 5284), sem erros novos no log.

## Lição
Manter o padrão: gerador expõe funções no escopo JS global e o painel do
widget as consome com `typeof fn === 'function'`. Toda mudança no JS do
gerador exige: regenerar `docs/grafo.html` + `_build_view()` + validar com
esprima (5 blocos) antes de reiniciar o widget.

## Conexoes

- [[cluster-hub-programacao]]