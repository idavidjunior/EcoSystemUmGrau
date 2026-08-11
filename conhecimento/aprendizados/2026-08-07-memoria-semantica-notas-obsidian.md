---
tipo: padrao
tags: [memoria, semantica, tf-idf, obsidian, busca, conhecimento]
data: 2026-08-07
contexto: Aprofundamento da memoria semantica do ecossistema a pedido do usuario.
decisao: O indice TF-IDF da memoria semantica passou a incluir as notas Obsidian.
impacto: Recuperacao por significado cobre memorias e notas; corpus BM25 mais completo.
---

# 2026-08-07 - Memoria semantica aprofundada com notas Obsidian

## Contexto

O usuario pediu para aprofundar a memoria semantica do ecossistema, cruzando as
notas Obsidian com a recuperacao de conhecimento.

## O que foi feito

1. **`scripts/memory_semantic.py`** agora indexa, alem das 125 memorias, as 475
   notas Obsidian de `conhecimento/notas/` e `conhecimento/aprendizados/`
   (source `nota`). O indice TF-IDF passou de 124 para 600 documentos.
2. **`_nota_texto()`** extrai titulo, tags do frontmatter e corpo (ate 2500 chars)
   de cada nota para indexacao; BOM removido para evitar erros de console.
3. **`search()`** retorna resultados com campo `source` (`mem` ou `nota`) — notas
   trazem o id `nota:<caminho>` e o titulo da nota.
4. **`mcp/memoria/habilidades/busca-conhecimento/search_knowledge.py`** corrigido:
   o corpus BM25 agora percorre `conhecimento/notas` E `conhecimento/aprendizados`
   (antes ignorava as 131 notas de aprendizados). Corpus: 883 documentos
   (475 notas + 283 knowledge graph + 125 memorias).

## Resultado

- Busca "controle da tv lg webos" retorna a nota correta com score 0.36.
- Busca "ponte caiu reconexao app android" retorna memorias e notas misturadas,
  incluindo os aprendizados de recuperacao rapida de conexao.
- A ponte carrega o modulo via importlib e usa o novo indice apos reinicio.

## Observacao

- A bridge em execucao mantem o modulo `memory_semantic` em cache por processo —
  reiniciar a bridge para ativar o novo indice com as notas.
- Preflight acusou divergencia de regras pre-existente (nao relacionada a esta
  tarefa); a Constituicao deployada precisa de `sync_rules.py update` em outra sessao.
