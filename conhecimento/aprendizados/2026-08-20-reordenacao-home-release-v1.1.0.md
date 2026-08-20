---
tipo: padrao
tags: [android, layout, toolbar, menu, reordenacao, release]
data: 2026-08-20
contexto: Adicionada função "Mover" na Home para personalizar a ordem das seções (atalhos, leitura, versículo, dicionário, notas, referências, recursos).
decisao: Inicialmente foi adicionado um botão TextView dentro do Toolbar (btnReorderHome) alterando o título para layout_width=0dp + weight=1. Isso quebrou o padrão de responsividade do projeto (todas as telas usam título match_parent + gravity center). Correção: reverter o título para o padrão e usar o mecanismo nativo de menu do Toolbar (android.widget.Toolbar + setActionBar + onCreateOptionsMenu + arquivo res/menu/home_menu.xml), seguindo o mesmo padrão do ReferenceMapActivity. A reordenação persiste em SharedPreferences via BibliaApplication.getHomeOrder/setHomeOrder (ids separados por vírgula) e é aplicada com applyHomeOrder() no onCreate movendo os views no homeSectionsContainer.
impacto: Botão "Mover" agora aparece no menu do Toolbar (ícone no canto direito) sem quebrar responsividade. Ordem das seções persiste após reiniciar o app. Release v1.1.0 (versionCode 2) assinado com release.keystore e instalado com adb install -r preservando dados.
---

# Pipeline de release e padrão de toolbar com menu

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
- "Salvar": persiste ids separados por vírgula em SharedPreferences (`BibliaApplication.setHomeOrder`).
- `applyHomeOrder()`: relê a ordem salva e reordena os views no container (removeView + addView).
- A ordem persistiu após reiniciar o app (testado).

## Release
- VersionCode 1 → 2, versionName 1.0.0 → 1.1.0 no AndroidManifest.xml.
- build.ps1 assina com release.keystore automaticamente (Test-Path).
- `adb install -r` preservou dados (ordem personalizada continuou após reinstalar).
- APK publicado: `releases/BibliaEstudoCompleta-v1.1.0.apk`.
