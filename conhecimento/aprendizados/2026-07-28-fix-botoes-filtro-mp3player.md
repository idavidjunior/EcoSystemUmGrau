# 2026-07-28: Botões de filtro sem texto visível — MaterialButton vs TextView

## Contexto
App Mp3Player Android. 5 botões de filtro no topo da aba "Músicas": Todas, Favoritas, A-Z, Lista, Sel. O texto não aparecia — os botões ficavam verdes uniformes sem nenhum texto visível.

## O que deu errado

### 1. Mudança de tema AppCompat â†’ MaterialComponents quebrou os botões
- `TagEditorActivity` usava `TextInputLayout` do Material Components, que REQUER tema `MaterialComponents`
- Ao trocar o tema de `AppCompat.DayNight.NoActionBar` para `MaterialComponents.DayNight.NoActionBar`, o `<Button>` passou a inflar como `MaterialButton` em vez de `AppCompatButton`
- `MaterialButton` aplica `backgroundTint` padrão (`@color/mtrl_btn_bg_color_selector`) que sobrescreve o `android:background` dos drawables customizados
- **Todos os botões ficaram verdes** (#1DB954) independente de active/inactive

### 2. `android:backgroundTint="@null"` é ignorado pelo MaterialButton
- MaterialButton só enxerga `app:backgroundTint`, não `android:backgroundTint`
- Tentativa de usar `android:backgroundTint` não surtiu efeito

### 3. MaterialButton tem padding interno que corta texto
- Mesmo com `android:insetLeft/Right="0dp"`, o MaterialButton mantém padding interno de ~20dp cada lado
- `layout_weight=1` dando ~68dp por botão â†’ sobram ~28dp para texto
- "Favoritas" (9 chars a 11sp) precisa de ~50dp â†’ só metade aparecia

## O que deu certo

### Solução definitiva: substituir `<Button>` por `<TextView>`
- TextView não tem `backgroundTint`, não tem padding interno de botão
- Atributos necessários: `android:clickable="true"` + `android:focusable="true"` + `android:gravity="center"`
- Mesmo `android:background="@drawable/..."` funciona sem interferência
- Precisa ajustar o tipo das variáveis no Kotlin de `Button` para `TextView`

### Processo de debugging que funcionou
1. **Print da tela + análise de pixels** com Python/Pillow — diagnóstico preciso
2. **uiautomator dump** para confirmar se o texto existe na árvore de View
3. **Teste de hipótese única por vez**: backgroundTint â†’ inset â†’ TextView

## Padrão para apps similares
- **Sempre que migrar de AppCompat para MaterialComponents**, verifique todos os `<Button>` — eles viram `MaterialButton` com comportamentos diferentes
- **Problema de texto invisível em botão?** Desconfie de `backgroundTint` primeiro
- **`?attr/` em drawables** funciona, mas a resolução depende do Context do tema correto
- **Prefira `TextView` sobre `Button`** para botões customizados com background drawable — evita toda a complexidade do MaterialButton
- **Ferramenta de diagnóstico:** `screencap` + Python/Pillow >> chutarç—…å›

## Conexoes

- [[cluster-hub-mp3player]]