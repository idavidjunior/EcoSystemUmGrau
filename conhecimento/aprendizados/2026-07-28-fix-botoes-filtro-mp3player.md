# 2026-07-28: BotÃµes de filtro sem texto visÃ­vel â€” MaterialButton vs TextView

## Contexto
App Mp3Player Android. 5 botÃµes de filtro no topo da aba "MÃºsicas": Todas, Favoritas, A-Z, Lista, Sel. O texto nÃ£o aparecia â€” os botÃµes ficavam verdes uniformes sem nenhum texto visÃ­vel.

## O que deu errado

### 1. MudanÃ§a de tema AppCompat â†’ MaterialComponents quebrou os botÃµes
- `TagEditorActivity` usava `TextInputLayout` do Material Components, que REQUER tema `MaterialComponents`
- Ao trocar o tema de `AppCompat.DayNight.NoActionBar` para `MaterialComponents.DayNight.NoActionBar`, o `<Button>` passou a inflar como `MaterialButton` em vez de `AppCompatButton`
- `MaterialButton` aplica `backgroundTint` padrÃ£o (`@color/mtrl_btn_bg_color_selector`) que sobrescreve o `android:background` dos drawables customizados
- **Todos os botÃµes ficaram verdes** (#1DB954) independente de active/inactive

### 2. `android:backgroundTint="@null"` Ã© ignorado pelo MaterialButton
- MaterialButton sÃ³ enxerga `app:backgroundTint`, nÃ£o `android:backgroundTint`
- Tentativa de usar `android:backgroundTint` nÃ£o surtiu efeito

### 3. MaterialButton tem padding interno que corta texto
- Mesmo com `android:insetLeft/Right="0dp"`, o MaterialButton mantÃ©m padding interno de ~20dp cada lado
- `layout_weight=1` dando ~68dp por botÃ£o â†’ sobram ~28dp para texto
- "Favoritas" (9 chars a 11sp) precisa de ~50dp â†’ sÃ³ metade aparecia

## O que deu certo

### SoluÃ§Ã£o definitiva: substituir `<Button>` por `<TextView>`
- TextView nÃ£o tem `backgroundTint`, nÃ£o tem padding interno de botÃ£o
- Atributos necessÃ¡rios: `android:clickable="true"` + `android:focusable="true"` + `android:gravity="center"`
- Mesmo `android:background="@drawable/..."` funciona sem interferÃªncia
- Precisa ajustar o tipo das variÃ¡veis no Kotlin de `Button` para `TextView`

### Processo de debugging que funcionou
1. **Print da tela + anÃ¡lise de pixels** com Python/Pillow â€” diagnÃ³stico preciso
2. **uiautomator dump** para confirmar se o texto existe na Ã¡rvore de View
3. **Teste de hipÃ³tese Ãºnica por vez**: backgroundTint â†’ inset â†’ TextView

## PadrÃ£o para apps similares
- **Sempre que migrar de AppCompat para MaterialComponents**, verifique todos os `<Button>` â€” eles viram `MaterialButton` com comportamentos diferentes
- **Problema de texto invisÃ­vel em botÃ£o?** Desconfie de `backgroundTint` primeiro
- **`?attr/` em drawables** funciona, mas a resoluÃ§Ã£o depende do Context do tema correto
- **Prefira `TextView` sobre `Button`** para botÃµes customizados com background drawable â€” evita toda a complexidade do MaterialButton
- **Ferramenta de diagnÃ³stico:** `screencap` + Python/Pillow >> chutarç—…å›

## Conexoes

- [[cluster-hub-mp3player]]