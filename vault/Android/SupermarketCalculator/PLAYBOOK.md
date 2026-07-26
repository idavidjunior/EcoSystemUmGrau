# Playbook: Do Pedido ao App Finalizado

## Como transformar uma ideia em um aplicativo Android funcional usando apenas SDK puro — e como replicar o processo para QUALQUER app

---

## O que este documento contém

Este não é um manual técnico (para isso existe o `METODOLOGIA.md`).  
Este é um **guia de processo** — a sequência real de passos, decisões e conversas que transformaram um pedido vago em um aplicativo completo, do zero até o APK final.

Você pode usar este roteiro como template para **qualquer aplicativo**: calculadora, lista de tarefas, inventário, pedidos, cardápio digital — o fluxo é sempre o mesmo.

---

## Índice do Processo

1. [Fase 0: A Pergunta Fundamental](#fase-0-a-pergunta-fundamental)
2. [Fase 1: Esqueleto — O mínimo que roda](#fase-1-esqueleto--o-mínimo-que-roda)
3. [Fase 2: Coração do App — A funcionalidade principal](#fase-2-coração-do-app--a-funcionalidade-principal)
4. [Fase 3: Persistência — Dados que não morrem](#fase-3-persistência--dados-que-não-morrem)
5. [Fase 4: Navegação — Múltiplas telas](#fase-4-navegação--múltiplas-telas)
6. [Fase 5: Personalização — Temas, skins, ajustes](#fase-5-personalização--temas-skins-ajustes)
7. [Fase 6: Refinamentos — UX, feedback, alerts](#fase-6-refinamentos--ux-feedback-alerts)
8. [Fase 7: Funcionalidades Avançadas](#fase-7-funcionalidades-avançadas)
9. [Fase 8: Release — Play Store](#fase-8-release--play-store)
10. [O Ciclo que se Repete em Todo App](#o-ciclo-que-se-repete-em-todo-app)
11. [Template de Conversa para Qualquer App](#template-de-conversa-para-qualquer-app)

---

## Fase 0: A Pergunta Fundamental

Antes de escrever UMA linha de código, o desenvolvedor precisa entender:

1. **Qual é o objetivo do app?**
2. **Quem vai usar?**
3. **Qual o fluxo principal?** (o usuário faz A → B → C)
4. **Quais dados são manipulados?**

No caso do **Supermercado Caixa**, as respostas foram:

> **Objetivo:** Uma calculadora de compras para supermercado. O usuário adiciona itens com preços, vê o total, define um orçamento e salva a lista.
>
> **Usuário:** Pessoas fazendo compras no supermercado.
>
> **Fluxo principal:** 
> 1. Abre o app
> 2. Digita o nome do produto (ou escolhe da lista)
> 3. Digita o preço no teclado numérico
> 4. Define a quantidade
> 5. Clica "ADICIONAR" → item aparece na lista
> 6. Vê o total atualizado
> 7. Finaliza a compra → vê o recibo → salva ou compartilha
>
> **Dados:** Itens (nome, preço unitário, quantidade), orçamento, listas salvas.

### Produto Mínimo Viável (MVP)

A **primeira versão** deve ter APENAS o essencial para o fluxo principal funcionar. Nada de temas, nada de skins, nada de abas, nada de personalização.

**MVP do Supermercado Caixa:**
- Tela única
- Numpad para digitar preço
- Campo para nome do produto
- Botão ADICIONAR
- Lista de itens com nome, qtd, unitário, total
- Total geral
- Botão FINALIZAR (mostra resumo em diálogo)

---

## Fase 1: Esqueleto — O mínimo que roda

### O que fazer

Criar a estrutura de diretórios, o build script, o AndroidManifest e um layout que mostre algo na tela.

### Sequência real

```
1. Criar pastas:
   src/com/supermarket/calculator/
   res/layout/
   res/values/
   res/drawable/

2. Criar AndroidManifest.xml (mínimo)
3. Criar res/values/strings.xml (só o nome do app)
4. Criar res/values/colors.xml (cores básicas)
5. Criar res/layout/activity_main.xml (um TextView "Hello World")
6. Criar src/.../MainActivity.java (setContentView)
7. Criar build.ps1 (o script que compila tudo)
8. Rodar build.ps1 → corrigir erros → até gerar APK
9. adb install -r MeuApp.apk → ver na tela
```

### Regra de ouro

> **Antes de avançar, o app precisa rodar.**  
> Se o build quebra, nada mais importa. Corrija o build primeiro.

### Lição para qualquer app

Sempre comece com:

```
build.ps1         → script de build
AndroidManifest   → declaração do app
strings.xml       → textos
colors.xml        → cores
activity_main.xml → layout principal
MainActivity.java → activity principal
```

Isso é o "Hello World" do SDK puro. Depois que roda, você incrementa.

---

## Fase 2: Coração do App — A funcionalidade principal

### O que fazer

Implementar o fluxo principal (A → B → C) que o usuário vai executar.

### Sequência real no Supermercado Caixa

#### Passo 2.1: Layout da calculadora
- LinearLayout vertical com:
  - Header (título)
  - Input area (nome do produto)
  - Teclado numérico (9 botões + 00 + , + ⌫ + C)
  - Botão ADICIONAR
  - ListView para os itens
  - Total geral
  - Botão LIMPAR e FINALIZAR

#### Passo 2.2: Modelo de dados
```java
public class CartItem {
    private String name;
    private double unitPrice;
    private int quantity;
}
```

#### Passo 2.3: Adapter da ListView
- `BaseAdapter` com layout de linha (nome, qtd, unitário, total, botão - e +)
- Interface de callback para ações: `onIncrement`, `onDecrement`, `onRemove`, `onItemClick`

#### Passo 2.4: Lógica do numpad
- Cada botão numérico adiciona um caractere a um `StringBuilder`
- O display mostra o valor formatado como moeda (R$ 0,00)
- ⌫ apaga o último dígito
- C limpa tudo

#### Passo 2.5: Merge de itens por nome
- Se o nome já existe na lista, incrementa a quantidade (não duplica)
- Se o nome está vazio, cria "Item 1", "Item 2"... (nunca mergeia)

### Perguntas que o usuário fez nesta fase

> "Quero uma calculadora de compras onde eu possa adicionar itens com preço, ver o total e finalizar a compra."

**Resposta:** Implementei o MVP descrito acima.

---

## Fase 3: Persistência — Dados que não morrem

### O que fazer

Quando o usuário fecha o app, os dados precisam sobreviver.

### Tipos de persistência no Supermercado Caixa

#### 3.1 Configurações (SharedPreferences)
- Tema escolhido
- Botões ocultos/mostrados
- Skin do teclado
- Itens customizados da lista de compras

#### 3.2 Listas salvas (arquivos no ExternalFilesDir)
- Quando o usuário finaliza a compra, salva um arquivo `.txt` com o recibo
- Também salva um `.json` estruturado com todos os itens (para carregar depois)
- Os arquivos ficam em `Android/data/com.supermarket.calculator/files/`

#### 3.3 Orçamento (SharedPreferences + memória)
- O limite de gasto é salvo nas preferências
- As flags de alerta (80%, 100%) são resetadas ao limpar o carrinho

### Pattern que se repete em qualquer app

```java
// Salvar (após cada alteração)
prefs.edit()
    .putString("chave", valor)
    .apply();

// Carregar (no onCreate)
String valor = prefs.getString("chave", "default");
```

---

## Fase 4: Navegação — Múltiplas telas

### O que fazer

Quando o app tem mais de uma função (calculadora + listas + configurações), precisa de navegação.

### Como foi feito no Supermercado Caixa

Em vez de usar Fragments (que exigem AndroidX), usei **FrameLayout com páginas**:

```xml
<FrameLayout layout_height="0dp" layout_weight="1">
    <LinearLayout android:id="@+id/calculatorPage" android:visibility="visible" />
    <LinearLayout android:id="@+id/savedListsPage" android:visibility="gone" />
    <ScrollView android:id="@+id/settingsPage" android:visibility="gone" />
</FrameLayout>
```

A troca é feita alternando `View.VISIBLE` / `View.GONE`:

```java
private void switchTab(int index) {
    calculatorPage.setVisibility(index == 0 ? View.VISIBLE : View.GONE);
    savedListsPage.setVisibility(index == 1 ? View.VISIBLE : View.GONE);
    settingsPage.setVisibility(index == 2 ? View.VISIBLE : View.GONE);
}
```

### Para qualquer app

Se o app tem até 5 telas, FrameLayout + visibilidade funciona perfeitamente.  
Não precisa de Fragments, Navigation Component, ViewPager — nada disso.

---

## Fase 5: Personalização — Temas, skins, ajustes

### O que fazer

O usuário pede para customizar a aparência e o comportamento.

### Sequência real

#### 5.1 Temas (Verde, Escuro, Azul)
- Cada tema é um conjunto de cores
- `applyTheme()` altera `setBackgroundColor()` e `setTextColor()` de cada view
- A escolha fica salva em SharedPreferences

#### 5.2 Skin do teclado (Padrão, Arredondado)
- Dois drawables XML diferentes: `btn_numpad.xml` e `bg_numpad_rounded.xml`
- `applySkin()` troca o background de todos os botões do numpad

#### 5.3 Personalizar teclado (ocultar botões)
- Checkboxes nas Config: "Mostrar ⌫", "Mostrar C", "Mostrar 00", "Mostrar operações"
- Em vez de `setVisibility(GONE)`, usa `setAlpha(0f)` + `setEnabled(false)`
- Isso mantém o grid alinhado (os botões continuam ocupando espaço, só ficam invisíveis)

### Pattern universal

```java
// Toda personalização segue o mesmo padrão:
// 1. UI de configuração (CheckBox, RadioGroup)
// 2. Salvar escolha (SharedPreferences)
// 3. Aplicar imediatamente (chamar método de apply)
// 4. Recarregar no onCreate()

chkOpcao.setOnCheckedChangeListener((b, checked) -> {
    config = checked;
    prefs.edit().putBoolean("chave", config).apply();
    aplicar();
});
```

---

## Fase 6: Refinamentos — UX, feedback, alerts

### O que fazer

Pequenos toques que fazem o app parecer profissional.

### Implementados no Supermercado Caixa

| Recurso | Como foi feito | Para que serve |
|---|---|---|
| Vibração ao atingir orçamento | `Vibrator` + `VibrationEffect` | Alerta físico sem depender de som |
| Alerta progressivo (80% → 100%) | Flags separadas `budgetWarned` / `budgetExceededWarned` | Avisa antes de estourar |
| Destaque do item sendo editado | `editingPosition` + cor de fundo diferente | O usuário vê qual item está editando |
| Edição inline do nome | `EditText` na lista + `TextWatcher` | Edita sem sair da tela |
| Botão FINALIZAR do mesmo tamanho | `wrap_content` + `paddingHorizontal` | Não fica desproporcional |
| Fonte do total maior | `textSize="20sp"` | Destaque visual |
| "Personalizar..." no fim da lista | Último item do array + diálogo extra | Usuário adiciona itens que faltam |

### Lição

> Cada refinamento é uma resposta a um problema real do usuário.  
> O usuário não pede "adicione destaque visual" — ele diz "não consigo ver qual item estou editando".

---

## Fase 7: Funcionalidades Avançadas

### O que fazer

Quando o app básico está funcionando, o usuário pede features mais elaboradas.

### Sequência real no Supermercado Caixa

#### 7.1 Lista pré-carregada de itens da cesta básica
O usuário pediu: "Quero uma lista com os itens da cesta básica já preenchidos para não precisar digitar tudo."

**Implementação:**
- Array de strings em `strings.xml` com ~60 itens (Arroz, Feijão, Café...)
- `AutoCompleteTextView` no campo de nome (+) botão ▼ que abre diálogo
- Itens já adicionados ao carrinho aparecem com ✅
- "Personalizar..." no final para adicionar itens que faltam

**Iteração:** O usuário testou e disse "não aparece a lista".  
**Bug:** O `rebuildGroceryAdapter()` criava a lista localmente mas não atualizava o array global.  
**Fix:** `allGroceryItems.clear(); allGroceryItems.addAll(merged);`

#### 7.2 Itens customizados permanentes
O usuário pediu: "Se eu digitar um item que não está na lista, quero que ele apareça nas próximas vezes."

**Implementação:**
- Salva itens customizados em SharedPreferences como JSON array
- `saveCustomGroceryItem()` → adiciona ao array + salva
- `loadCustomGroceryItems()` → carrega no início
- `rebuildGroceryAdapter()` → mescla defaults + customizados

#### 7.3 Salvar lista como modelo reutilizável
O usuário pediu: "Quero salvar minha lista de compras para usar de novo."

**Implementação:**
- Ao finalizar, opção "Salvar como modelo"
- Salva JSON estruturado em arquivo com prefixo `modelo_`
- Aba "Modelos" com botão "Salvar carrinho atual como modelo"
- Tocar em um modelo → carrega itens no carrinho

#### 7.4 Comparação entre listas salvas
O usuário pediu: "Quero comparar duas listas para ver o que mudou."

**Implementação:**
- Aba "Comparar" dentro de Listas
- Dois spinners para selecionar listas JSON
- Algoritmo de comparação:
  - Itens em comum (com diff de preço: ↑ mais caro, ↓ mais barato)
  - Itens apenas na lista 1 (removidos)
  - Itens apenas na lista 2 (adicionados)
  - Comparação de total geral

#### 7.5 Adicionar todos os itens de uma vez
O usuário pediu: "Quero adicionar a lista inteira de uma vez e depois ir preenchendo os preços."

**Implementação:**
- Botão "Adicionar todos" no diálogo da lista
- Adiciona todos os itens com preço 0 e qtd 1
- Usuário clica em cada linha para editar preço

#### 7.6 Carregar lista salva para editar
O usuário pediu: "Quero pegar uma lista que salvei e editá-la."

**Implementação:**
- Botão "Carregar" (ícone de lápis) para cada arquivo JSON na lista
- Também botão "Carregar" no diálogo de visualização
- Carrega todos os itens no carrinho → usuário edita normalmente

---

## Fase 8: Release — Play Store

### O que fazer

Preparar o app para publicação.

### Sequência real

1. **Gerar keystore de release:**
   ```powershell
   keytool -genkey -v -keystore release.keystore -alias supermarket `
       -keyalg RSA -keysize 2048 -validity 10000
   ```

2. **Atualizar AndroidManifest.xml:**
   - `versionCode="1"`
   - `versionName="1.0.0"`
   - `android:debuggable="false"`

3. **Atualizar build.ps1:**
   - Parâmetro `-Release` que usa o release.keystore
   - Modo debug usa o debug.keystore padrão do Android SDK

4. **Build release:**
   ```powershell
   .\build.ps1 -Release
   ```

5. **Verificar assinatura:**
   ```powershell
   apksigner verify SupermarketCalculator-release.apk
   ```

6. **Assets para Play Console:**
   - Ícone 512×512px
   - Feature graphic 1024×500px
   - Screenshots
   - Descrição

---

## O Ciclo que se Repete em Todo App

Este é o padrão que se repetiu em CADA funcionalidade do Supermercado Caixa — e se repete em QUALQUER app:

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│   │ USUÁRIO  │    │ DEV      │    │ CÓDIGO   │          │
│   │ DESCREVE │───▶│ ENTENDE  │───▶│ ESCREVE  │          │
│   │ O QUE    │    │ PLANEJA  │    │ EDITA    │          │
│   │ QUER     │    │ ONDE     │    │          │          │
│   └──────────┘    │ ALTERAR  │    └──────────┘          │
│                   └──────────┘         │                 │
│                                        ▼                 │
│                               ┌──────────────┐           │
│                               │ BUILD        │           │
│                               │ (aapt+java+   │           │
│                               │  d8+apksigner)│           │
│                               └──────────────┘           │
│                                        │                 │
│                                        ▼                 │
│                               ┌──────────────┐           │
│                    ┌─────────│ INSTALAR     │           │
│                    │         │ (adb install) │           │
│                    │         └──────────────┘           │
│                    │                  │                  │
│                    ▼                  ▼                  │
│               ┌──────────┐    ┌──────────────┐          │
│               │ CORRIGIR │    │ TESTAR       │          │
│               │ BUG      │◀───│ (USUÁRIO     │          │
│               │          │    │  EXPERIMENTA)│          │
│               └──────────┘    └──────────────┘          │
│                                        │                 │
│                                        ▼                 │
│                               ┌──────────────┐           │
│                               │ FUNCIONOU?   │           │
│                               │ SIM → PRÓXIMA│           │
│                               │ NÃO → VOLTA  │           │
│                               └──────────────┘           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Quanto tempo dura cada ciclo?

No Supermercado Caixa:

| Etapa | Tempo típico |
|---|---|
| Usuário descreve | 1–3 frases |
| Dev entende e planeja | 1–2 minutos |
| Escrever/editar código | 2–10 minutos |
| Build | 10–30 segundos |
| Instalar | 5–10 segundos |
| Testar | 30 segundos a 2 minutos |
| Corrigir bug | 1–5 minutos |

**Ciclo total: 5–20 minutos por funcionalidade.**

---

## Template de Conversa para Qualquer App

Este é o script de conversa que você (usuário) e eu (dev) seguimos.  
Você pode usar este template para QUALQUER aplicativo que quiser construir.

### Passo 1: Definição inicial

> **Você:** Quero criar um app de [tipo de app].  
> Ele faz [descrição de 1–2 frases].  
> O principal fluxo é: [passo A → passo B → passo C].

> **Dev:** Entendi. Vou criar a estrutura inicial com:
> - Build script
> - Tela principal com [funcionalidade principal]
> - [Dados que o app manipula]

### Passo 2: Primeira versão

> **Dev:** App está rodando. Aqui está o que funciona:
> - [Feature 1]
> - [Feature 2]
> - [Feature 3]
>
> Teste e me diga o que quer mudar ou adicionar.

### Passo 3: Iterações

> **Você:** Quero adicionar [nova funcionalidade].

> **Dev:** Vou implementar. Onde no código:
> - [Arquivo 1] → adicionar [o quê]
> - [Arquivo 2] → modificar [o quê]
>
> Build + instalar + testar.

### Passo 4: Refinamentos

> **Você:** [Problema específico que encontrou ao testar].

> **Dev:** Identifiquei a causa: [explicação do bug].  
> Corrigindo: [o que mudou no código].  
> Build + instalar + testar novamente.

### Passo 5: Release

> **Você:** Quero publicar na Play Store.

> **Dev:** Vou gerar o keystore, atualizar versão, build release.  
> Você precisa desses assets: [lista].

---

## Resumo: O Que Levar para OUTRO App

Cada passo deste playbook se aplica a QUALQUER aplicativo Android com SDK puro:

| Fase | Aplica-se a | Exemplos |
|---|---|---|
| Esqueleto (build + manifest) | **Todo app** | Calculadora, Lista, Pedidos, Cardápio |
| Funcionalidade principal | **Todo app** | O que o app faz de único |
| Persistência (salvar dados) | **Todo app** | Configurações, histórico, dados |
| Navegação (múltiplas telas) | Apps com 2+ telas | Config, lista detalhada |
| Personalização (temas/skins) | Apps com UI customizável | Qualquer app que o usuário queira customizar |
| UX refinamentos | **Todo app** | Feedback visual, alerts, destaque |
| Funcionalidades avançadas | Apps maduros | Comparação, modelos, exportação |
| Release/Play Store | **Todo app publicado** | Keystore, assets, versionamento |

### A habilidade mais importante

> **Saber identificar o que o usuário REALMENTE quer dizer** quando ele faz um pedido.

Exemplos reais deste projeto:

| O usuário disse | O que significava | O que implementei |
|---|---|---|
| "Não aparece a lista" | Bug: `allGroceryItems` não estava sendo populado | `allGroceryItems.clear(); allGroceryItems.addAll(merged)` |
| "Quero adicionar tudo de uma vez" | Botão no diálogo que adiciona todos os itens | `builder.setNeutralButton("Adicionar todos", ...)` |
| "Quero editar listas salvas" | Carregar itens no carrinho para modificar | Botão "Carregar" que chama `loadStructuredListIntoCart()` |
| "Os itens adicionados devem aparecer marcados" | ✅ na frente dos itens já no carrinho | `inCart[i] = true; displayItems[i] = "✅ " + rawItems[i]` |

---

> *Documentado em 14/07/2026 com base no desenvolvimento completo do Supermercado Caixa — do primeiro pedido ao APK final.*
