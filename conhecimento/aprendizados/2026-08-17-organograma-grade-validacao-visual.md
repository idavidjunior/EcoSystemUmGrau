# 2026-08-17: Organograma agrupado por livro + técnicas de validação visual via adb

**Categoria:** padrao
**Tags:** organograma, layout, validacao-visual, adb, android
**Data:** 2026-08-17

## Contexto

O mapa de referências cruzadas "Eufrates" (30 nós, 0 conexões) renderizava como uma faixa branca gigante no lugar do organograma. O usuário pediu para implementar a visão de agrupar por livro quando não há conexões, e depois para aprender com os erros/acertos para evoluir.

## Problema (o que não funcionou)

1. O layout agrupado original posicionava cada livro em uma coluna com `colSpacing = availableWidth / groupCount`. Com 29 livros, o espaçamento caía para ~34px, menor que a largura da caixa (150px). Resultado: todas as caixas sobrepunham na mesma faixa horizontal, formando um retângulo branco gigante.
2. `ReferenceMapView.setData()` era chamado no onCreate com `getWidth()==0` e `getHeight()==0`, então o layout inicial usava viewWidth=0 e a escala ficava errada. `onSizeChanged` chamava `setViewSize` mas NÃO reaplicava `fitToScreen`.
3. O `getContentBounds` original não incluía os títulos dos livros nem os barramentos, então o `fitToScreen` cortava o topo do conteúdo.
4. TeamViewer (pacote `com.teamviewer.teamviewer.market.mobile`) aparece no foreground intermitentemente no device, corrompendo screenshots e interceptando toques.

## Solução (o que funcionou)

### Grade profissional (organograma de verdade)
- `layoutBookGroupsVertical`: `colsPerRow = max(1, (int)((availableWidth + colGap) / (boxW + colGap)))` com colGap=30f; quebra em múltiplas fileiras (`rowCount = ceil(groupCount/colsPerRow)`).
- Cada livro = coluna com versículos empilhados (`rowSpacing = boxH + 14f`); se exceder `maxRowHeight`, compacta para caber.
- `rowTopY` guarda o Y do topo de cada fileira; `bookGroupRow` mapeia livro→fileira.
- Conectores estilo org-chart: tronco vertical do root + um barramento horizontal por fileira + linhas verticais para cada coluna. Usa `R.color.divider`.
- `drawBookGroupTitles`: nome do livro em texto bold acima da primeira caixa do grupo (vertical); rotacionado -90° no modo horizontal.
- `getContentBounds` override: inclui 60px extra acima da primeira fileira para títulos/barramentos.
- `ReferenceMapView.onSizeChanged`: passou a chamar `fitToScreen()` após `setViewSize(w,h)`.

### Técnica de validação visual sem ver a imagem (CRÍTICO)
O modelo não vê screenshots. Pipeline que funciona:
1. `adb shell screencap -p /sdcard/x.png` + pull.
2. Analisar pixels com PowerShell `System.Drawing`:
   - Caixas = branco puro `255,255,255`.
   - Bordas das caixas = accent `#C9A84C` (201,168,76).
   - Divisores/conectores = `#E5E0D8` (229,224,216).
   - Fundo da view = `245,243,238`.
3. Verificar `mCurrentFocus` com `dumpsys window` — se mostra TeamViewer, trazer app à frente com `input keyevent 4` + `am start -n com.biblia.estudo/.ui.crossref.ReferenceMapActivity`.
4. Após reinstalar APK, o seletor de mapa abre; tocar em (540,1300) seleciona "Eufrates". Sempre checar o dump do uiautomator antes de tocar.
5. Contar "runs" de pixels brancos por linha para detectar caixas separadas (5 runs = 5 colunas espaçadas).

## Impacto

- Mapa sem conexões agora renderiza como organograma de grade legível: root no topo, tronco vertical, barramentos por fileira, colunas por livro, títulos de livros visíveis, caixas 150x52 com referência (bold 12f) e versículo truncado (9f).
- FitToScreen recalcula após resize, conteúdo centralizado e sem corte.
- Técnica de validação por pixels permite iterar em UI Android sem visão humana.

## Referências

- `OrganogramLayoutEngine.java` (buildHierarchy, buildBookGroups, layoutBookGroupsVertical/Horizontal, drawBookGroupConnectors, drawBookGroupTitles, getContentBounds)
- `BaseLayoutEngine.java` (drawNode caixa arredondada, getNodeBoxWidth/Height, truncateToWidth, setTextColorFor)
- `ReferenceMapView.java` (onSizeChanged → fitToScreen, ScaleListener, GestureListener)
- `LayoutManager.java` (setData/setViewSize → initialize + computeLayout)
