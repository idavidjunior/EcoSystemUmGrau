---
tags: [decisao, dinâmica, hierarquia, opencode, persistir, reais]
aliases: [Importação de pasta preservando árvore + remoção de referênc]
date: 2026-08-09
---

# Importação de pasta preservando árvore + remoção de referência

**Fonte:** opencode

## Problema
- Importar uma pasta adicionava só os arquivos de primeiro nível (achatados) ou usava navegação dinâmica sem persistir a hierarquia.
- Remoção podia confundir-se com exclusão de arquivo real.

## Decisão
- `user_resources` ganhou a coluna `parent_id` (0 = raiz da biblioteca; >0 = id da pasta referenciada pai).
- `UserResourceDao`:
  - `importFolderTree(cr, treeUri, parentId)` — importa a árvore inteira (subpastas + arquivos) com nomes reais; idempotente via índice único `(uri, type)` (reutiliza linhas, evita órfãos).
  - `getChildren(id)` — filhos diretos (pastas primeiro, depois arquivos, alfabético).
  - `getRootResources()` — itens na raiz (parent_id=0/NULL).
  - `deleteSubtree(id)` — remove nó + descendentes do banco (referências apenas).
  - `importChildrenForFolder(id, cr)` — materializa filhos sob demanda ao navegar (legado/parcial).
- `ResourcesActivity` navega a árvore com pilha de pastas + item "← Voltar"; "+ Importar Pasta" usa `ACTION_OPEN_DOCUMENT_TREE`; remoçã
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]