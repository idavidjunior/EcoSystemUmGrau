---
tags: [decisao, dinâmica, opencode, tocar, tratar, type]
aliases: [Importação de pasta preservando árvore + remoção de referênc]
date: 2026-08-21
---

# Importação de pasta preservando árvore + remoção de referência

**Fonte:** opencode

---
tipo: decisao
tags: [biblia, biblioteca, saf, arvore, referencia]
data: 2026-08-09
contexto: BibliaEstudoCompleta — importação de pastas e gerenciamento da biblioteca de recursos.
decisao: Persistir a hierarquia real das pastas importadas via SAF (coluna parent_id) e tratar remoção como exclusão apenas das referências no banco.
impacto: Navegação em árvore (subpastas com nomes reais), remoção sem tocar nos arquivos do dispositivo, importação idempotente por (uri,type).
---

# Importação de pasta preservando árvore + remoção de referência

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
- `ResourcesActivity` navega a árvore com pilha de pastas + item "← Voltar"; "+ Importar Pasta" usa `ACTION_OPEN_DOCUMENT_TREE`; remoção confirma e usa `deleteSubtree`.
- `HomeActivity` long-press em pasta usa `deleteSubtree` para evitar órfãos.

## Impacto
- O usuário vê a estrutura real de pastas na biblioteca.
- Remover do app nunca apaga arquivos originais do dispositivo (só referências no SQLite).
- Build completo (aapt + javac + d8 + apksigner) passou.

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]