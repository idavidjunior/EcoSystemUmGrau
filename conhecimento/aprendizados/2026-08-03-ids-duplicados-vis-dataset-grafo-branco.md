---
tipo: erro
tags: [widget, grafo, vis-network, obsidian, data-set, debug]
data: 2026-08-03
---

# Bug grafo em branco — ids duplicados no vis.DataSet

## Contexto
O widget desktop (pywebview + vis-network) abria mas o grafo ficava em branco:
o `#net` existia com tamanho correto, mas nenhum canvas era criado e nenhum
erro aparecia nos logs.

## Causa raiz
O gerador (`generate-graph-html.py`) usava o nome do arquivo (stem) como id do
nó. 9 notas existem em duas pastas de categoria diferentes (ex:
`cognitivo/2026-07-27-correcao-dos-4-pontos-finais-do-ecossistema.md` e
`missoes/...md`), gerando ids duplicados.

O `new vis.DataSet([...])` lança `Cannot add item: id already exists` na
primeira duplicata. Como a criação da rede está no mesmo `<script>` que o
`const container`/`const network`, a exceção aborta TODO o bloco antes de
qualquer coisa ser criada → canvas vazio, e como o erro acontece no próprio
bloco principal, o `window.onerror` tardio do API_INJECT (registrado no fim do
body) não pegava nada.

## Correção
Em `extrair_nos()` do `generate-graph-html.py`, `add_no` agora verifica se o id
já existe em `nos_por_id` e reutiliza a nota existente (retorna `nos_por_id[nid]`)
em vez de adicionar uma duplicata. Resultado: 291 notas → 282 nós únicos.

Também foi adicionado um `early_error` handler no `<head>` (antes do bloco
principal rodar) que acumula erros em `window.__widgerrs`, para que um
`evaluate_js` externo consiga ver o erro real — e um probe
(`scripts/dbg_probe2.py`) que usa `win.evaluate_js` para inspecionar canvas e
erros.

## Impacto
O grafo do widget voltou a renderizar (282 nós, 1199 conexões). O aprendizado:
erros dentro do `<script>` que cria a rede abortam silenciosamente tudo — o
diagnóstico precisa capturar erro no próprio bloco (via listener no `<head>`)
ou via `evaluate_js`, nunca por handler registrado depois no body.

## Conexoes

- [[cluster-hub-programacao]]