---
tags: [alterado, opencodeopencodeopencode, padrao, quebrou, responsividade, weight]
aliases: [Pipeline de release e padrão de toolbar com menu]
date: 2026-08-20
---

# Pipeline de release e padrão de toolbar com menu

**Fonte:** opencode+opencode+opencode

## Problema encontrado
O botão "Mover" adicionado como TextView dentro do Toolbar, com o título alterado para weight=1, quebrou o padrão de responsividade do projeto. Todas as outras telas usam título com `layout_width="match_parent"` + `gravity="center"`.

## Padrão correto para ação no Toolbar
1. Título permanece `match_parent` + `gravity="center"` (não alterar para weight).
2. Criar `res/menu/<tela>_menu.xml` com o item e ícone.
3. Na Activity: `setActionBar(findViewById(R.id.toolbar))` no onCreate.
4. Implementar `onCreateOptionsMenu` (inflate do menu) e `onOptionsItemSelected`.
5. Ícone de menu aparece no canto direito do Toolbar, título permanece centralizado.

Referência de padrão no projeto: `ReferenceMapActivity.java` + `res/menu/reference_map_menu.xml`.

## Reordenação das seções da Home
- Lista fixa de seções em `getHomeSections()` (ids dos views no `homeSectionsContainer`).
- `showReorderDialog()`: ListView em AlertDialog; toque em item move para cima (troca de posição).
- 
## Conexoes

- [[aegis-registrado-como-projeto-irmao-rust]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-teste-do-vigilante-automático]]
- [[padrao-hub-padroes]]