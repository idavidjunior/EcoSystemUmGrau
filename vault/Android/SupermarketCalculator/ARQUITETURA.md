# Arquitetura do Supermercado Caixa

## Stack
- **Linguagem:** Java 8 (Android API 36)
- **Build:** `aapt` + `javac` + `jar` + `d8` + `zipalign` + `apksigner` (via `build.ps1`)
- **UI:** XML layouts + `Activity` única com páginas em `FrameLayout`
- **Estado:** Variáveis em memória + `SharedPreferences` + arquivos JSON em `ExternalFilesDir`
- **SDK:** Android puro — sem AndroidX, sem Gradle, sem Kotlin

## Estrutura de Diretórios
```
res/
  drawable/         — XML drawables (shapes, seletores, ícone launcher)
  layout/           — activity_main.xml, cart_item.xml, saved_list_item.xml
  values/           — strings.xml (193 linhas), colors.xml (34 cores), styles.xml
  layout-v22/       — mesmos XMLs com elevation/sombra (auto-gerado pelo aapt)

src/com/supermarket/calculator/
  MainActivity.java       — 2233 linhas, toda a lógica
  adapter/CartAdapter.java — 154 linhas, adapter do carrinho
  models/CartItem.java     — 28 linhas, modelo de item do carrinho
```

## Arquitetura de Abas (4 páginas)

### Estrutura XML
```
LinearLayout (root)
  ├── LinearLayout (headerBar — título fixo)
  ├── LinearLayout (tabBar — 4 abas)
  └── FrameLayout (mainContent — layout_weight=1)
       ├── LinearLayout calculatorPage        — Tab 0: Calculadora
       ├── LinearLayout expensesPage           — Tab 1: Despesas (file browsers)
       │   ├── LinearLayout (sub-tab bar: Compras de Mercado | Despesas Financeiras)
       │   └── FrameLayout
       │       ├── LinearLayout expMarketContent       — Sub-tab 0: market files
       │       └── LinearLayout expFinanceFilesContent  — Sub-tab 1: expense files
       ├── LinearLayout savedListsPage         — Tab 2: Listas (expense CRUD)
       │   └── LinearLayout expFinanceContent
       │       ├── Input row (desc + amount + categoria + add)
       │       ├── ListView (expenseListView)
       │       ├── Budget row (financeBudgetRow)
       │       └── Total row (expenseTotalDisplay)
       └── ScrollView settingsPage             — Tab 3: Config
```

### Mapeamento Tab -> Conteúdo
| Índice | Tab label | Page ID | Conteúdo |
|--------|-----------|---------|----------|
| 0 | Calculadora | calculatorPage | Numpad + cart + total + budget |
| 1 | Despesas | expensesPage | Sub-tabs: market files + expense files |
| 2 | Listas | savedListsPage | Expense CRUD form + list + budget + total |
| 3 | Config | settingsPage | Temas, skin, personalizar teclado |

### Sub-tabs (dentro de Despesas - Tab 1)
| Índice | Nome | View ID | Conteúdo |
|--------|------|---------|----------|
| 0 | Compras de Mercado | expMarketContent | ListView de arquivos `lista_compras_*` e `modelo_*` |
| 1 | Despesas Financeiras | expFinanceFilesContent | ListView de `despesas.json` e `despesas_*.json` |

### Navegação
```java
switchTab(index):
  - Alterna VISIBLE/GONE das 4 páginas
  - Aplica/remove bg_tab_active nas abas
  - Ajusta alpha (1.0 ativa, 0.6 inativa)
  - Tab 1 → refreshExpensesMarket() + refreshFinanceFiles()
   - Tab 2 → refreshExpenseTotal() (sem loadExpensesFromFile — forma inicia vazia)

switchListasSubTab(index):
  - Toggle expMarketContent (0) / expFinanceFilesContent (1)
  - Toggle expTabMarket / expTabFinance active state
  - Sub-tab 0 → refreshExpensesMarket()
  - Sub-tab 1 → refreshFinanceFiles()
```

## Modelos de Dados

### CartItem (carrinho de compras)
```java
CartItem(String name, double unitPrice, int quantity)
  - getName(), setName()
  - getUnitPrice(), setUnitPrice()
  - getQuantity(), setQuantity(int) — Math.max(0, qty)
  - increment() / decrement() — qtd mínima 1
  - getTotal() = unitPrice * quantity
```

### ExpenseItem (despesas financeiras)
```java
ExpenseItem(String description, double amount, String category)
  - description, amount, category (String)
  - date (long — System.currentTimeMillis())
```

## Persistência

### SharedPreferences
- `settings`: theme (int), skin (int), showOps/Back/Clear/00 (boolean)
- `supermarket_prefs`: custom_categories (JSON array), custom_grocery_items (JSON array), finance_budget_limit (float)

### Arquivos JSON em `listas_pessoais/`
```
ExternalFilesDir(null)/listas_pessoais/
  ├── lista_compras_YYYY-MM-DD_HH-mm-ss.json  — Listas de compras salvas
  ├── modelo_YYYY-MM-DD_HH-mm-ss.json          — Modelos reutilizáveis
  ├── despesas.json                             — Despesas correntes (sempre sobrescrito)
  └── despesas_YYYY-MM-DD_HH-mm-ss.json        — Relatórios de despesas exportados (via "Salvar")
```

### Estrutura JSON: lista de compras
```json
{
  "date": "2026-07-18_10-30-00",
  "prefix": "lista_compras",
  "title": "Lista de compras - 18/07/2026 10:30",
  "items": [
    {"name": "Arroz", "unitPrice": 5.99, "quantity": 2, "total": 11.98}
  ],
  "total": 11.98
}
```

### Estrutura JSON: despesas
```json
{
  "version": 1,
  "title": "Despesas Financeiras - 18/07/2026 10:30",
  "date": "2026-07-18_10-30-00",
  "prefix": "despesas",
  "expenses": [
    {"description": "Conta de luz", "amount": 150.00, "category": "Luz", "date": 1721234567890}
  ]
}
```

## Fluxo de Dados: Calculadora

### Input -> Carrinho
1. Usuário digita nome (ou seleciona da AutoCompleteTextView / diálogo de compras)
2. Digita preço no numpad → priceBuffer (StringBuilder) → priceDisplay (formatado R$)
3. Ajusta quantidade (+/-)
4. Clica ADICIONAR:
   - addOrUpdateItem():
     - Se nome vazio → "Item N" + contadorSemNome → não mergeia
     - Se nome existe → mergeOrAddAtTop() (soma quantidade)
     - Se nome novo → add no topo da lista
   - Reseta input (priceBuffer, qty=1)

### Edição Inline no Carrinho
1. Toca em uma linha → onItemClick() → loadItemForEditing(position)
   - Carrega nome no input, zera priceBuffer (usuário digita novo preço)
   - editingIndex = position
   - adapter.setEditingPosition(position) → destaca linha
2. Edita nome inline (EditText na lista vira focusable)
3. Clica ADICIONAR novamente → updateItemInPlace(position) → atualiza item existente
4. Toca em outra linha ou fora → editingIndex = -1, remove destaque

### Merge Strategy
- Se nome vazio → SEMPRE cria novo item (não mergeia)
- Se nome existe na lista → encontra pelo nome, soma quantidades, NÃO soma preços
- Se nome novo → adiciona no topo (position 0)
- mergeOrAddAtTop() é o método central

### Finalizar Compra (finishPurchase)
1. Se carrinho vazio → alerta
2. Mostra diálogo com 4 botões:
   - **Salvar**: showSaveTitleDialog() → saveListToFile (.txt) + saveStructuredList (prefix="lista_compras")
   - **Modelo**: showSaveTitleDialog() com prefix="modelo" → saveStructuredList()
   - **Despesa**: saveCartAsExpense() → cria ExpenseItem com descrição concatenada + total + categoria "Compras"
   - **OK**: Apenas clearCartAfterFinish()
3. Após Salvar/Modelo → clearCartAfterFinish() (limpa flags, itens, input)

## Fluxo de Dados: Despesas Financeiras

### Adicionar Despesa
1. Usuário preenche descrição (opcional) e valor
2. Clica "Categorias" ou botão "+" → showCategorySelector()

### Category Selector (dual-mode)
- **Single tap** em uma categoria → addExpenseWithCategory(categoria) imediatamente + fecha diálogo
- **Long press** em uma categoria → ativa multi-select mode:
  - Toast avisa: "Modo múltiplo ativado"
  - Usuário toca em várias categorias
  - Clica "Aplicar" → cria UMA despesa com categorias concatenadas por "/"
- Opção "+ Adicionar categoria" → showAddCategoryDialog()
- Default (sem categoria explícita) → addExpense() → addExpenseWithCategory("Outros")

### Inline Editing na Lista de Despesas
- **Tocar na linha**: alterna editingExpensePosition (highlight + editável)
- **Tocar no nome**: edita descrição inline (TextWatcher → saveExpensesToFile())
- **Tocar no valor** (totalTv): diálogo para editar amount
- **Tocar na categoria** (unitTv): diálogo para selecionar nova categoria
- **Botão de deletar**: confirmação → remove → saveExpensesToFile()

### Relatório por Categoria
- showExpenseReport() → agrupa todas as despesas por categoria
- Exibe: valor total por categoria + percentual do total geral
- Diálogo de leitura

### Salvar / Exportar
- **Salvar** (expenseExportBtn → showSaveExpenseDialog()):
  - Exibe diálogo com campo de título (padrão: "Despesas Financeiras - dd/MM/yyyy HH:mm")
  - Salva em despesas_YYYY-MM-DD_HH-mm-ss.json com título, data, prefix e expenses
  - "Salvar e continuar": salva e permanece na aba Listas
  - "Apenas Salvar": salva e navega para aba Despesas (Tab 1)
- **Auto-save** (inline editing): saveExpensesToFile() → escreve em despesas.json (working file)

## Fluxo de Dados: Listas de Mercado (multi-selection)

### Tela: Despesas > Compras de Mercado
1. Lista arquivos `lista_compras_*.json` e `modelo_*.json`
2. Ações por item: **Carregar** (→ calculadora), **Compartilhar**, **Excluir**
3. **Long press** em um item → enterMarketSelectionMode()
   - Mostra barra de seleção com campo de valor e botões "Aplicar" / "X"
   - Checkboxes aparecem nos itens
   - Usuário seleciona um ou mais itens
   - Digita valor, clica "Aplicar" → cria ExpenseItem com nomes concatenados + valor digitado

### Tela: Despesas > Despesas Financeiras
1. Lista `despesas.json` + `despesas_*.json`
2. Botão **Carregar** → loadExpensesFromFile(f) com o arquivo específico + switchTab(2)
3. Títulos são extraídos do JSON via `extractTitleFromJson()` e exibidos no lugar do nome do arquivo
4. **Compartilhar** / **Excluir** com confirmação

### showSavedFileContent() — Preview Dialog
- Lê JSON e mostra conteúdo formatado
- Se tem "expenses" → mostra como descrição [categoria]: valor
- Se tem "items" → mostra como item x qtd unitário = total + TOTAL
- Botão **"Editar"**: se expenses → loadExpensesFromFile(f) (carrega o arquivo específico) + switchTab(2); se items → loadStructuredListIntoCart() + switchTab(0)
- Botão **"Renomear"**: updateJsonTitle() — altera o campo "title" no JSON

### Pattern: Form Starts Empty (Crítico)
- **Tab 2 (Listas)** sempre inicia VAZIA — sem loadExpensesFromFile em switchTab ou setupExpenses
- Dados só são carregados quando o usuário explicitamente clica "Editar" no navegador de arquivos
- Comportamento idêntico à calculadora: começa zerada, pronto para novos cálculos
- `loadExpensesFromFile()` aceita um parâmetro `File` para carregar qualquer arquivo, não só despesas.json

### Pattern: Limpar = Screen Only
- Botão "Limpar" na tela de despesas NUNCA salva no arquivo
- `expenseItems.clear()` → notifyDataSetChanged → refreshExpenseTotal — sem saveExpensesToFile()
- Arquivo JSON permanece intacto; Toast avisa "Tela limpa. Dados salvos permanecem intactos."

## Temas (3 temas programáticos)

| Tema | rootLayout | headerBar | tabBar | totalDisplay |
|------|-----------|-----------|--------|--------------|
| Verde (default) | #F0F0F0 | #1B5E20 (primaryDark) | #1B5E20 | #1B5E20 |
| Escuro | #121212 | #1a1a1a | #0d0d0d | #FFFFFF |
| Azul | #F0F0F0 | #0D47A1 (blueDark) | #0D47A1 | #1565C0 |

### Skin do Teclado
- **Padrão**: `btn_numpad.xml` (cantos 4dp) / `btn_action.xml`
- **Arredondado**: `bg_numpad_rounded.xml` (cantos 12dp) / `bg_action_rounded.xml`
- Aplicado via `setBackgroundResource()` em todos os botões do numpad

## Categorias de Despesas (14 base + custom)

### Base (em strings.xml)
Água, Luz, Gás, Telefone, Internet, Aluguel, Condomínio, Farmácia, Transporte, Educação, Lazer, Seguro, Assinaturas, Outros

### Custom Categories
- Persistidas em `supermarket_prefs` como JSON array na key `custom_categories`
- Carregadas em `loadCustomCategories()` (SharedPreferences)
- `getAllCategories()` → merge base + custom
- Adicionadas via "Adicionar categoria" no seletor

## Orçamento Financeiro (financeBudgetLimit)
- Persistido como `finance_budget_limit` (float) em `supermarket_prefs`
- Configurado via showFinanceBudgetDialog() — diálogo EditText
- Exibido em financeBudgetRow (clicável)
- Cálculo: remaining = limit - totalDespesas
- Cor verde se remaining >= 0, vermelha se negativo

## Lista de Compras Pré-carregada (60+ itens)
- String-array `grocery_items` em strings.xml
- AutoCompleteTextView no input de nome
- Botão ▼ → showGroceryListSelection() — diálogo com checkboxes
- Itens já no carrinho aparecem com "✅ "
- "Personalizar..." no final → showAddCustomItemDialog()
- Itens customizados salvos em SharedPreferences (key `custom_grocery_items`, JSON array)
- rebuildGroceryAdapter() → mescla defaults + customizados

## Build Pipeline (build.ps1)

```
1. aapt package → Gera R.java no diretório src/
2. javac → Compila .java → .class (src → build/classes/)
3. jar → Empacota classes → build/classes.jar
4. d8 → Converte .jar → .dex (build/dex/)
5. aapt package → Empacota recursos SEM DEX → build/-unsigned.apk
6. aapt add → Adiciona classes.dex ao APK
7. zipalign → Alinha em 4 bytes → -aligned.apk
8. apksigner → Assina com keystore → APK final
```

### Parâmetros
- **`-Release`**: usa `release.keystore` (senha `opencode`, alias `supermarket`)
- **Default**: usa `debug.keystore` do Android SDK (`~/.android/debug.keystore`)

## Padrões e Convenções

### Nomenclatura
- Views: camelCase sem prefixo (productNameInput, priceDisplay, cartList)
- Métodos: camelCase com verbo prefixado (setupNumpad, addOrUpdateItem, loadExpensesFromFile)
- Constantes: UPPER_SNAKE_CASE com prefixo KEY_ (KEY_THEME, KEY_SKIN)
- IDs XML: camelCase com tipo sufixo (btnN0, productNameInput, cartList, priceDisplay)
- Arquivos JSON: prefixo_timestamp.json (lista_compras_2026-07-18_10-30-00.json)

### Pattern: Edição Inline
1. **editingPosition** no adapter controla qual linha está editável
2. getView(): `position == editingPosition` → focusable+highlight / senão → label mode
3. TextWatcher com `setTag()`/`getTag()` para evitar leaks
4. Alternar background entre `highlightBg` e `rowEven`/`rowOdd`

### Pattern: Alternar Visibilidade mantendo Grid
```java
setButtonHidden(Button btn, boolean hidden):
  setVisibility(VISIBLE) + setAlpha(hidden ? 0 : 1) + setEnabled(!hidden) + setClickable(!hidden)
```
Em vez de `setVisibility(GONE)`, que quebra o layout.

### Pattern: TextWatcher Management
```java
Object tag = editText.getTag();
if (tag instanceof TextWatcher) editText.removeTextChangedListener((TextWatcher) tag);
editText.setText(valor);
TextWatcher watcher = new TextWatcher() { ... };
editText.addTextChangedListener(watcher);
editText.setTag(watcher);
```
Sempre remover o watcher antigo antes de setText() para evitar loop infinito.

### Pattern: Dual-mode Dialogs
Usado no Category Selector:
```java
setOnItemClickListener: single tap → ação imediata
setOnItemLongClickListener: ativa modo multi-select → altera comportamento do single tap
```
A flag `isMultiSelect[0]` (array de 1 elemento, necessário por ser acessada em inner class) controla o modo.

### Pattern: Refresh em switchTab()
Cada tab faz refresh de dados voláteis ao ser ativada. **Tab 2 (Listas) NÃO auto-carrega do arquivo** — começa vazia:
```java
if (index == 1) { refreshExpensesMarket(); refreshFinanceFiles(); }
if (index == 2) { refreshExpenseTotal(); }  // sem loadExpensesFromFile
```

### Compatibilidade Retroativa (API < 23)
```java
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
    view.setBackgroundColor(context.getColor(R.color.nome));
} else {
    view.setBackgroundColor(context.getResources().getColor(R.color.nome));
}
```

### Vibração
```java
Vibrator v = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
    v.vibrate(VibrationEffect.createWaveform(pattern, -1));
} else {
    v.vibrate(pattern, -1);
}
```

## Decisões de Design

1. **SDK puro** → zero dependências, build rápido (~15s), controle total, sem risco de breaking changes
2. **Activity única** → sem Fragments, navegação via visibilidade, estado compartilhado em variáveis
3. **Arquivos JSON** → persistência simples, legível, editável fora do app, sem overhead de SQLite
4. **SharedPreferences imediato** → salvar configurações no momento da alteração (não só em onPause)
5. **StringBuilder para preço** → controle granular da formatação, evita problemas de ponto flutuante no display
6. **Numpad programático** → listeners em código em vez de onClick no XML (mais flexível para temas/skins)
7. **Merge por nome** → evita duplicatas na lista de compras, mas NUNCA mergeia itens sem nome
8. **Sub-tabs via visibilidade** → mesma técnica das tabs principais, sem componentes extras
9. **FrameLayout com layout_weight** → conteúdo ocupa espaço restante, header+tabbar fixos
10. **ShowSavedFileContent com "Editar"** → botão dinâmico que detecta tipo do JSON (expenses vs items)

## Como Estender o App

### Adicionar uma nova aba
1. XML: adicionar novo TextView em tabBar + nova página em FrameLayout
2. Java: findViewById() + switchTab() case + setupTabs() listener
3. Atualizar ARQUITETURA.md se aplicável

### Adicionar novo tipo de dado persistido
1. Definir estrutura JSON
2. Criar métodos saveXxx() / loadXxx() em MainActivity
3. Usar getListasDir() para o diretório de arquivos
4. Registrar refresh no switchTab() se necessário

### Adicionar novo tema
1. Adicionar cores em colors.xml
2. Adicionar case em applyTheme()
3. Adicionar RadioButton no settingsPage
4. Adicionar constante THEME_NOVA

### Adicionar nova categoria padrão
1. Adicionar string em strings.xml (exp_cat_nova)
2. Adicionar entrada no array em getAllCategories()

---

> Documentado em 18/07/2026 — Supermercado Caixa v1.0
