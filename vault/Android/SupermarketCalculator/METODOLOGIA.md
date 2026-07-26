# Metodologia de Desenvolvimento Android (Sem AndroidX/Gradle)

Este documento registra todo o processo utilizado para construir o **Supermercado Caixa** do zero — desde a estrutura de diretórios até a publicação na Play Store. A abordagem serve para **qualquer aplicativo Android** que use apenas o SDK puro, sem Gradle, AndroidX ou Kotlin.

---

## Índice

1. [Filosofia Geral](#1-filosofia-geral)
2. [Estrutura do Projeto](#2-estrutura-do-projeto)
3. [Build System](#3-build-system)
4. [AndroidManifest.xml](#4-androidmanifestxml)
5. [Recursos (Resources)](#5-recursos-resources)
6. [Código Java](#6-código-java)
7. [Processo de Desenvolvimento Iterativo](#7-processo-de-desenvolvimento-iterativo)
8. [Depuração e Log](#8-depuração-e-log)
9. [Build e Instalação](#9-build-e-instalação)
10. [Publicação na Play Store](#10-publicação-na-play-store)
11. [Lições Aprendidas e Padrões Reutilizáveis](#11-lições-aprendidas-e-padrões-reutilizáveis)
12. [Cobrindo as Brechas](#12-cobrindo-as-brechas--e-se-precisar-de-recyclerview--camera--fcm)

---

## 1. Filosofia Geral

### 1.1 Princípios

- **SDK puro**: zero dependências externas. Apenas `android.jar` da plataforma alvo.
- **Build manual**: sem Gradle, sem Maven, sem AndroidX. `aapt` + `javac` + `d8` + `apksigner`.
- **Iteração rápida**: ciclo curto de editar → build → `adb install -r` → testar.
- **Compatibilidade retroativa**: minSdkVersion baixo (21), usar compatibilidade manual quando necessário.

### 1.2 Stack tecnológica

| Componente | Tecnologia |
|---|---|
| Linguagem | Java 8 (android.jar API 36) |
| Build | PowerShell script + aapt + javac + jar + d8 + zipalign + apksigner |
| UI | XML layouts + View programática (sem DataBinding) |
| Estado | SharedPreferences + variáveis em memória |
| Persistência | Internal storage / ExternalFilesDir (arquivos texto) |
| Navegação | ViewFlipper / FrameLayout com páginas + visibilidade |

---

## 2. Estrutura do Projeto

```
meu-app/
├── AndroidManifest.xml       # Declaração do app
├── build.ps1                 # Script de build
├── release.keystore          # Keystore de produção (NÃO COMMITAR)
├── src/                      # Código-fonte Java
│   └── com/meuapp/
│       ├── MinhaActivity.java
│       ├── adapter/
│       │   └── MeuAdapter.java
│       └── models/
│           └── MeuModelo.java
├── res/                      # Recursos
│   ├── drawable/             # XML drawables (formas, seletores)
│   ├── layout/               # XML layouts
│   ├── values/
│   │   ├── colors.xml
│   │   ├── strings.xml
│   │   └── styles.xml
│   └── layout-v22/           # Overrides para API 22+ (opcional)
├── build/                    # Gerado pelo script (não versionar)
└── MeuApp.apk                # APK final
```

### 2.1 Diretório `src/`

O diretório `src/` segue a estrutura de pacotes Java padrão:

```
src/
  com/
    meudominio/
      meuapp/
        MainActivity.java          # Tela principal
        adapter/
          CartAdapter.java          # Adaptador de ListView
          ListaAdapter.java         # Outro adaptador
        models/
          CartItem.java             # Classe de modelo
```

### 2.2 Diretório `res/`

```
res/
  drawable/          # Formas XML (botões, backgrounds, ícones)
  layout/            # Telas XML
  values/            # strings.xml, colors.xml, styles.xml
  layout-v22/        # Versões de layout para API 22+ (ex: sombra com elevation)
```

---

## 3. Build System

### 3.1 Script `build.ps1`

O script de build executa 8 etapas sequenciais:

```
1. aapt  → Gera R.java (referências de recursos)
2. javac → Compila .java → .class
3. jar   → Empacota .class → .jar
4. d8    → Converte .jar → .dex (Dalvik Executable)
5. aapt  → Empacota recursos → unsigned.apk
6. aapt  → Adiciona classes.dex ao APK
7. zipalign → Alinha o APK (4-byte alignment)
8. apksigner → Assina o APK
```

### 3.2 Parâmetros do script

| Parâmetro | Default | Descrição |
|---|---|---|
| `-OutputName` | `SupermarketCalculator` | Nome base do APK gerado |
| `-Release` | `$false` | Usa `release.keystore` para assinar |

### 3.3 Estrutura do build.ps1

```powershell
param([string]$OutputName = "MeuApp", [switch]$Release = $false)

$ANDROID_HOME = $env:ANDROID_HOME
$BT = "$ANDROID_HOME\build-tools\36.0.0"
$PLATFORM = "$ANDROID_HOME\platforms\android-36\android.jar"

# Escolher keystore conforme modo
if ($Release) {
    $KEYSTORE = "$pwd\release.keystore"
    $STOREPASS = "sua-senha"
    $KEYALIAS = "seu-alias"
} else {
    $KEYSTORE = "$env:USERPROFILE\.android\debug.keystore"
    $STOREPASS = "android"
    $KEYALIAS = "androiddebugkey"
}

# Criar diretórios temporários
New-Item -ItemType Directory -Path "$BuildDir\classes", "$BuildDir\dex" -Force | Out-Null

# 1. Gerar R.java
aapt package -f -m -M AndroidManifest.xml -S res -I "$PLATFORM" -J src

# 2. Compilar Java
javac -cp "$PLATFORM" -d "$BuildDir\classes" $srcFiles

# 3. Criar JAR
jar cf "$BuildDir\classes.jar" -C "$BuildDir\classes" .

# 4. Converter para DEX
d8 --lib "$PLATFORM" --release --output "$BuildDir\dex" "$BuildDir\classes.jar"

# 5. Empacotar APK (sem DEX)
aapt package -f -M AndroidManifest.xml -S res -I "$PLATFORM" -F "$BuildDir\unsigned.apk"

# 6. Adicionar DEX ao APK
cd "$FullBuildDir"; aapt add unsigned.apk classes.dex

# 7. Alinhar
zipalign -f -v 4 "$BuildDir\unsigned.apk" "$BuildDir\aligned.apk"

# 8. Assinar
apksigner sign --ks "$KEYSTORE" --ks-pass pass:$STOREPASS --ks-key-alias $KEYALIAS "$BuildDir\aligned.apk"

Copy-Item "$BuildDir\$ApkName-aligned.apk" "$ApkName.apk" -Force
```

### 3.4 Próximos passos para evoluir o build

- Adicionar `-v` (versionCode/versionName) via parâmetro
- Adicionar ofuscação com `proguard` (requer `proguard.jar`)
- Adicionar split por densidade de tela
- Adicionar CI/CD (GitHub Actions) que executa `build.ps1 -Release`

---

## 4. AndroidManifest.xml

### 4.1 Estrutura básica

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.meudominio.meuapp"
    android:versionCode="1"
    android:versionName="1.0.0">

    <uses-sdk android:minSdkVersion="21" android:targetSdkVersion="36" />

    <uses-permission android:name="android.permission.VIBRATE" />
    <!-- outras permissões aqui -->

    <application
        android:allowBackup="true"
        android:icon="@drawable/ic_launcher"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:theme="@style/AppTheme"
        android:debuggable="false">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:windowSoftInputMode="adjustResize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

### 4.2 Regras importantes

| Atributo | Valor | Motivo |
|---|---|---|
| `android:versionCode` | Sempre incrementar | Play Store usa para comparar versões |
| `android:versionName` | `1.0.0` (semantic versioning) | Exibido para o usuário |
| `android:debuggable` | `false` no release | Segurança |
| `android:exported="true"` | Na launcher activity | Necessário desde Android 12 |
| `android:windowSoftInputMode` | `adjustResize` | Evita que teclado sobreponha layouts |
| Permissões normais | `android.permission.VIBRATE` | Concedidas automaticamente na instalação |

### 4.3 Sobre `android:exported`

Desde Android 12 (API 31), toda activity com `<intent-filter>` **deve** ter `android:exported` explícito. O valor é:
- `"true"` se outras apps podem iniciar a activity (launcher, deep links)
- `"false"` se apenas o próprio app inicia

---

## 5. Recursos (Resources)

### 5.1 `res/values/colors.xml`

Definir cores como constantes nomeadas para facilitar temas:

```xml
<resources>
    <color name="primary">#2E7D32</color>
    <color name="primaryDark">#1B5E20</color>
    <color name="background">#F0F0F0</color>
    <color name="cardBg">#FFFFFF</color>
    <color name="textPrimary">#212121</color>
    <color name="textSecondary">#757575</color>
    <!-- + cores específicas para orçamento, destaque, etc -->
</resources>
```

Padrão: usar `getResources().getColor(R.color.nome)` para acessar no código.

### 5.2 `res/values/strings.xml`

TODOS os textos do app devem estar em `strings.xml`. Isso permite:
- Tradução futura
- Manutenção centralizada
- Consistência

### 5.3 `res/values/styles.xml`

```xml
<resources>
    <style name="AppTheme" parent="@android:style/Theme.Material.Light.NoActionBar">
        <item name="android:colorPrimary">@color/primary</item>
        <item name="android:colorPrimaryDark">@color/primaryDark</item>
    </style>
</resources>
```

> **Atenção**: Como não usamos AndroidX, o parent deve ser do Android framework (`@android:style/...`).

### 5.4 Drawables XML

Drawables XML substituem imagens bitmap para ícones e backgrounds:

**Botão de teclado** (`btn_numpad.xml`):
```xml
<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:state_pressed="true">
        <shape android:shape="rectangle">
            <solid android:color="#E0E0E0" />
            <corners android:radius="4dp" />
        </shape>
    </item>
    <item>
        <shape android:shape="rectangle">
            <solid android:color="#FAFAFA" />
            <stroke android:width="0.5dp" android:color="#E0E0E0" />
            <corners android:radius="4dp" />
        </shape>
    </item>
</selector>
```

**Variação de skin**: criar um segundo drawable com cantos mais arredondados (`bg_numpad_rounded.xml`) e alternar via `setBackgroundResource()`.

### 5.5 Layouts XML

Estrutura geral de layout para qualquer app:

```xml
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:background="@color/background">

    <!-- HEADER (fixo no topo) -->
    <LinearLayout android:layout_height="wrap_content" ... />

    <!-- TAB BAR (navegação entre páginas) -->
    <LinearLayout android:id="@+id/tabBar" ... />

    <!-- CONTEÚDO PRINCIPAL (ocupa espaço restante) -->
    <FrameLayout
        android:layout_width="match_parent"
        android:layout_height="0dp"
        android:layout_weight="1">

        <!-- Página 1 -->
        <LinearLayout android:id="@+id/page1" ... />

        <!-- Página 2 (invisível inicialmente) -->
        <LinearLayout android:id="@+id/page2" android:visibility="gone" ... />

        <!-- Página 3 (invisível inicialmente) -->
        <ScrollView android:id="@+id/page3" android:visibility="gone" ... />
    </FrameLayout>
</LinearLayout>
```

### 5.6 Técnica de Tab Switching

Cada "aba" é uma página dentro de um `FrameLayout`. A troca é feita via visibilidade:

```java
private void switchTab(int index) {
    page1.setVisibility(index == 0 ? View.VISIBLE : View.GONE);
    page2.setVisibility(index == 1 ? View.VISIBLE : View.GONE);
    page3.setVisibility(index == 2 ? View.VISIBLE : View.GONE);

    // Atualizar aparência da tab ativa
    tab1.setAlpha(index == 0 ? 1f : 0.6f);
    tab1.setBackgroundResource(index == 0 ? R.drawable.bg_tab_active : 0);
    // ... repetir para cada tab
}
```

O `FrameLayout` com `layout_weight="1"` garante que a página ativa ocupe todo o espaço disponível.

---

## 6. Código Java

### 6.1 Estrutura de uma Activity

```java
public class MainActivity extends Activity implements Adaptador.Listener {

    // 1. Views
    private EditText nomeInput;
    private TextView displayPreco;
    private ListView listaView;

    // 2. Dados
    private List<MeuItem> itens = new ArrayList<>();
    private MeuAdapter adapter;
    private int indiceEditando = -1;

    // 3. Configurações
    private SharedPreferences prefs;

    // 4. Serviços de sistema
    private Vibrator vibrator;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        prefs = getSharedPreferences("config", MODE_PRIVATE);
        vibrator = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);

        initViews();
        setupListeners();
        setupLista();
        carregarEstado();
    }
}
```

### 6.2 Padrão Adapter para ListView

**Interface de callback** (define quais ações o adapter pode disparar):

```java
public interface Listener {
    void onItemClick(int position);
    void onIncrementar(int position);
    void onRemover(int position);
    void onNomeAlterado(int position, String nome);
}
```

**Adapter** (controla a exibição de cada linha):

```java
public class MeuAdapter extends BaseAdapter {
    private final Context context;
    private final List<MeuItem> itens;
    private final Listener listener;
    private int posicaoEditando = -1;

    public void setEditingPosition(int pos) {
        if (posicaoEditando != pos) {
            int old = posicaoEditando;
            posicaoEditando = pos;
            if (old >= 0) notifyDataSetChanged();
            if (pos >= 0) notifyDataSetChanged();
        }
    }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
        if (convertView == null) {
            convertView = LayoutInflater.from(context)
                .inflate(R.layout.item_lista, parent, false);
        }

        // Configurar views da linha...
        // Destacar se for a posição editando
        if (position == posicaoEditando) {
            convertView.setBackgroundColor(corDestaque);
        } else {
            convertView.setBackgroundColor(alternarCores(position));
        }

        // Botões da linha
        botaoRemover.setOnClickListener(v -> listener.onRemover(position));
        convertView.setOnClickListener(v -> listener.onItemClick(position));

        return convertView;
    }
}
```

### 6.3 Edição Inline (na própria lista)

Para editar um campo diretamente na ListView:

1. No XML da linha, usar `EditText` estilizado como label (`background="@null"`, sem cursor, não-focusable)
2. No `getView()`, quando `position == posicaoEditando`:
   - `editText.setFocusable(true)`
   - `editText.setCursorVisible(true)`
   - `editText.setBackgroundResource(R.drawable.bg_input)`
3. Caso contrário: reverter para aparência de label
4. Adicionar `TextWatcher` no EditText para salvar alterações em tempo real:
   ```java
   TextWatcher watcher = new TextWatcher() {
       final int pos = position;
       @Override
       public void afterTextChanged(Editable s) {
           if (listener != null && pos == posicaoEditando) {
               listener.onNomeAlterado(pos, s.toString());
           }
       }
   };
   editText.addTextChangedListener(watcher);
   editText.setTag(watcher); // para remover depois
   ```

### 6.4 Teclado Numpad Programático

Em vez de `android:onClick` no XML, registrar listeners no código:

```java
private void setupNumpad() {
    View.OnClickListener listener = v -> {
        String val = null;
        int id = v.getId();
        if (id == R.id.btn0) val = "0";
        else if (id == R.id.btn1) val = "1";
        // ... etc
        if (val != null) handleInput(val);
    };

    int[] ids = {R.id.btn0, R.id.btn1, ..., R.id.btn9};
    for (int id : ids) {
        findViewById(id).setOnClickListener(listener);
    }

    // Botões de operação (+, -, ×, ÷, =)
    findViewById(R.id.btnSoma).setOnClickListener(v -> handleOperator("+"));
    findViewById(R.id.btnIgual).setOnClickListener(v -> handleEquals());
}
```

**Operações encadeadas** (calculadora inline):

```java
private double operando1 = 0;
private String opPendente = null;

private void handleOperator(String op) {
    if (opPendente != null) {
        double atual = getCurrentValue();
        operando1 = evaluate(operando1, atual, opPendente);
    } else {
        operando1 = getCurrentValue();
    }
    bufferPreco.setLength(0);
    opPendente = op;
    updateDisplay();
}

private double evaluate(double a, double b, String op) {
    switch (op) {
        case "+": return a + b;
        case "−": return a - b;
        case "×": return a * b;
        case "÷": return (b != 0) ? a / b : 0;
        default: return b;
    }
}
```

### 6.5 Gerenciamento de Estado com SharedPreferences

```java
// Salvar
prefs.edit()
    .putInt("tema", temaAtual)
    .putBoolean("mostrar_ops", mostrarOps)
    .putString("nome_usuario", nome)
    .apply(); // assíncrono

// Carregar
temaAtual = prefs.getInt("tema", 0); // 0 = default
mostrarOps = prefs.getBoolean("mostrar_ops", false);
```

### 6.6 Temas Programáticos

Aplicar tema alterando cores das views diretamente:

```java
private void applyTheme() {
    switch (temaAtual) {
        case TEMA_ESCURO:
            layoutRoot.setBackgroundColor(corPreto);
            headerBar.setBackgroundColor(corCinzaEscuro);
            textDisplay.setTextColor(corBranco);
            break;
        case TEMA_AZUL:
            layoutRoot.setBackgroundColor(corFundo);
            headerBar.setBackgroundColor(corAzulEscuro);
            textDisplay.setTextColor(corAzul);
            break;
        default: // Verde
            layoutRoot.setBackgroundColor(corFundo);
            headerBar.setBackgroundColor(corVerdeEscuro);
            textDisplay.setTextColor(corVerde);
            break;
    }
}
```

### 6.7 Vibração

```java
private void vibrar() {
    Vibrator v = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
    if (v == null || !v.hasVibrator()) return;
    long[] pattern = {0, 400, 100, 400};
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
        v.vibrate(VibrationEffect.createWaveform(pattern, -1));
    } else {
        v.vibrate(pattern, -1);
    }
}
```

### 6.8 Compatibilidade retroativa (API < 26)

Sempre verificar `Build.VERSION.SDK_INT >= Build.VERSION_CODES.XX` antes de usar APIs modernas:

```java
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
    view.setBackgroundColor(context.getColor(R.color.nome));
} else {
    view.setBackgroundColor(context.getResources().getColor(R.color.nome));
}
```

---

## 7. Processo de Desenvolvimento Iterativo

### 7.1 Ciclo de cada funcionalidade

```
1. ENTENDER → O usuário descreve o que quer
2. PLANEJAR → Onde no código isso afeta? Quais arquivos?
3. IMPLEMENTAR → Escrever/editar código
4. BUILD → build.ps1
5. INSTALAR → adb install -r
6. TESTAR → Usar o app no dispositivo
7. REPETIR → Se algo não funcionar, corrigir e voltar ao passo 3
```

### 7.2 Sequência real seguida neste projeto

| Fase | O que foi feito | Técnica usada |
|---|---|---|
| 1 | Estrutura inicial + build.ps1 + layout base | AndroidManifest, LinearLayout aninhados, numpad |
| 2 | ListView + Adapter + CartItem | BaseAdapter + interface de callback |
| 3 | Input area + merge de itens | Editar nome/preço, mesclar por nome |
| 4 | Botão finalizar + recibo | StringBuilder, diálogo AlertDialog |
| 5 | Ícone launcher | Vector drawable XML |
| 6 | Orçamento (budget) + vibração | SharedPreferences, Vibrator, alertas em % |
| 7 | Aviso progressivo (80% → 100%) | Flags separadas por threshold |
| 8 | Salvar lista + compartilhar | FileOutputStream, Intent.ACTION_SEND |
| 9 | Abas (Calculadora / Listas / Config) | FrameLayout + visibilidade |
| 10 | Temas (Verde, Escuro, Azul) | applyTheme() programático |
| 11 | Skin do teclado (Padrão, Arredondado) | setBackgroundResource() alternativo |
| 12 | Botões de operações | Calculadora inline com operand1 + pendingOp |
| 13 | Personalizar teclado (ocultar botões) | setAlpha(0) + setEnabled(false) para manter grid |
| 14 | Edição inline do nome | EditText na lista + TextWatcher |
| 15 | Destaque do item em edição | highlightBg + editingPosition no adapter |
| 16 | Keystore release + build.ps1 Release | keytool + apksigner com keystore próprio |

### 7.3 Como lidar com bugs

1. **Identificar o bug**: o usuário descreve o comportamento inesperado
2. **Reproduzir mentalmente**: percorrer o fluxo de código
3. **Localizar a causa**: usar `Log.d()` para rastrear valores
4. **Corrigir**: editar o código
5. **Verificar**: rebuild + reinstalar + testar

Exemplo real: "ao remover um item, o destaque de edição não atualizava"

```java
// ANTES (bug):
if (editingIndex == position) editingIndex = -1;
else if (editingIndex > position) editingIndex--;

// DEPOIS (corrigido):
if (editingIndex == position) {
    editingIndex = -1;
    adapter.setEditingPosition(-1); // ← faltava notificar o adapter
} else if (editingIndex > position) {
    editingIndex--;
    adapter.setEditingPosition(editingIndex); // ← atualizar destaque
}
```

---

## 8. Depuração e Log

### 8.1 Uso de `Log.d()`

Inserir logs nos pontos-chave:

```java
Log.d("MinhaTag", "onCreate chamado");
Log.d("MinhaTag", "adicionando item: nome=" + nome + " preco=" + preco);
Log.d("MinhaTag", "editando posição=" + position);
```

Visualizar com:
```powershell
adb logcat -s MinhaTag
```

### 8.2 Comandos úteis para debug

```powershell
# Ver logs do app
adb logcat -s SuperCalc:* *:S

# Instalar APK
adb install -r MeuApp.apk

# Ver lista de pacotes
adb shell pm list packages | Select-String "meuapp"

# Forçar parada
adb shell am force-stop com.meudominio.meuapp

# Limpar dados
adb shell pm clear com.meudominio.meuapp

# Capturar tela
adb shell screencap /sdcard/screen.png
adb pull /sdcard/screen.png
```

---

## 9. Build e Instalação

### 9.1 Pré-requisitos

- Android SDK (command-line tools + build-tools 36.0.0 + platform android-36)
- JDK 8+ (javac, jar, keytool)
- PowerShell (Windows) ou bash (Linux/Mac)

### 9.2 Build

```powershell
# Debug (teste)
.\build.ps1

# Release (produção)
.\build.ps1 -Release
```

Saída:
- `SupermarketCalculator-debug.apk` — assinado com debug keystore
- `SupermarketCalculator-release.apk` — assinado com release keystore

### 9.3 Instalação em dispositivo

```powershell
# Com fio USB
adb install -r SupermarketCalculator-debug.apk

# Wireless (ADB over TCP/IP)
adb tcpip 5555
adb connect 192.168.1.100:5555
adb install -r SupermarketCalculator-debug.apk
```

### 9.4 Verificação do APK assinado

```powershell
apksigner verify SupermarketCalculator-release.apk
apksigner verify --print-certs SupermarketCalculator-release.apk
```

---

## 10. Publicação na Play Store

### 10.1 Gerar keystore de release

```powershell
keytool -genkey -v -keystore release.keystore `
    -alias seu-alias `
    -keyalg RSA -keysize 2048 -validity 10000 `
    -storepass sua-senha -keypass sua-senha `
    -dname "CN=NomeApp, OU=Developer, O=SuaEmpresa, L=Cidade, ST=Estado, C=BR"
```

⚠️ **IMPORTANTE**: guardar em local seguro! Sem ele não é possível publicar atualizações.

### 10.2 Assets necessários no Play Console

| Asset | Especificação |
|---|---|
| Ícone | 512×512px PNG (adaptável: 32 bits) |
| Feature graphic | 1024×500px PNG |
| Screenshots | 2–8 screenshots (mín. 2), 1080×1920px ou similar |
| Descrição curta | 80 caracteres |
| Descrição completa | Máx. 4000 caracteres |

### 10.3 Checklist pré-publicação

- [ ] `versionCode` incremental no `AndroidManifest.xml`
- [ ] `android:debuggable="false"`
- [ ] APK assinado com release keystore
- [ ] Testar APK release em dispositivo físico
- [ ] Verificar permissões (só as necessárias)
- [ ] Ter política de privacidade (se o app coleta dados)
- [ ] Preço (grátis ou pago?)
- [ ] Categorização correta no Play Console

---

## 11. Lições Aprendidas e Padrões Reutilizáveis

### 11.1 O que funciona bem sem AndroidX

| Funcionalidade | Como implementar |
|---|---|
| Listas com ações | BaseAdapter + interface de callback |
| Navegação por abas | FrameLayout + visibilidade |
| Temas | applyTheme() programático |
| Diálogos | AlertDialog.Builder |
| Compartilhar | Intent.ACTION_SEND |
| Salvar arquivos | FileOutputStream / SharedPreferences |
| Sensores/Vibração | Vibrator, VibrationEffect |
| Teclado customizado | Botões em grid + listeners programáticos |
| Edição inline | EditText + TextWatcher + alternar focusable |

### 11.2 O que NÃO funciona (ou é difícil) sem AndroidX

| Funcionalidade | Motivo | Alternativa |
|---|---|---|
| ViewBinding/DataBinding | Requer AndroidX | `findViewById()` manual |
| Fragments com backstack | Fragment nativo é limitado | ViewFlipper + pilha manual |
| Navigation Component | AndroidX only | Gerenciar manualmente |
| Material Design 3 | AndroidX only | Tema Material via styles.xml |
| RecyclerView | AndroidX only (ou v7) | ListView (mais simples, suficiente) |
| ConstraintLayout | Lib extra | LinearLayout aninhados |
| LiveData/ViewModel | AndroidX only | Variáveis + onSaveInstanceState |
| Room Database | AndroidX only | SQLiteOpenHelper + arquivos texto |

### 11.3 Padrões que se repetem em qualquer app

**1. Alternar visibilidade de botões mantendo o grid:**

Em vez de `setVisibility(GONE)` (que remove o espaço e quebra o alinhamento), usar:

```java
private void setButtonHidden(Button btn, boolean hidden) {
    btn.setVisibility(View.VISIBLE);
    btn.setAlpha(hidden ? 0f : 1f);
    btn.setEnabled(!hidden);
    btn.setClickable(!hidden);
}
```

**2. Atualizar UI após mudanças:**

```java
private void atualizarTudo() {
    adapter.notifyDataSetChanged();
    recalcularTotal();
    atualizarDisplayOrcamento();
}
```

**3. Persistir estado das configurações:**

Sempre salvar em `onPause()` ou imediatamente após cada alteração:

```java
chkOpcoes.setOnCheckedChangeListener((b, checked) -> {
    configOpcoes = checked;
    salvarConfiguracoes();
    aplicarCustomizacao();
});
```

**4. Interface de comunicação Activity ↔ Adapter:**

```java
public interface CartListener {
    void onIncrement(int position);
    void onDecrement(int position);
    void onRemove(int position);
    void onItemClick(int position);
    void onNameChanged(int position, String name);
}
```

**5. Evitar merge de itens sem nome (criar IDs únicos):**

```java
if (nome.isEmpty()) {
    contadorSemNome++;
    nome = "Item " + contadorSemNome;
    itens.add(0, new Item(nome, preco, qtd));
    // Não chama mergeOrAddAtTop() — não mesclar itens sem nome
} else {
    mergeOrAddAtTop(new Item(nome, preco, qtd));
}
```

**6. Reset de flags de alerta ao limpar dados:**

```java
private void limparTudo() {
    itens.clear();
    contadorSemNome = 0;
    flagAlerta80 = false;
    flagAlerta100 = false;
    adapter.notifyDataSetChanged();
    recalcular();
    resetarInput();
}
```

### 11.4 Fluxo de desenvolvimento recomendado para qualquer app

```
1.  build.ps1 + AndroidManifest.xml simples   → "Hello World" rodando
2.  Layout principal + atividade              → UI estrutural
3.  Modelo de dados                           → O que o app manipula
4.  ListView + Adapter                        → Exibir dados
5.  Input + Ações                             → Adicionar/editar/remover
6.  Persistência                              → Salvar/carregar
7.  Navegação (abas ou telas)                 → Organizar funcionalidades
8.  Configurações + Temas                     → Personalização
9.  Ajustes finos de UX                       → Vibração, destaques, alerts
10. Build release + keystore + Play Console   → Publicar
```

Cada passo é testado com `build.ps1` + `adb install -r` antes de passar ao próximo.

### 11.5 Considerações finais

- Usar SDK puro sem AndroidX é **viável para apps de médio porte** e tem a vantagem de zero dependências, build rápido e controle total.
- A técnica de edição inline na lista + teclado numérico customizado funciona bem para **apps de entrada de dados** (calculadoras, inventário, pedidos, formulários).
- O padrão de **abas com FrameLayout** substitui Fragments para apps com poucas telas.
- **SharedPreferences + arquivos texto** substituem banco de dados para apps com dados simples.
- A **metodologia iterativa** (entender → codificar → build → testar → repetir) é o coração do processo: cada ciclo dura segundos, não minutos.

---

## 12. Cobrindo as Brechas — E Se Precisar de RecyclerView / Camera / FCM?

A metodologia cobre apps de médio porte com SDK puro. Se surgir a necessidade de algo que o SDK não oferece, eis as estratégias para cada caso:

### 12.1 RecyclerView (quando ListView não basta)

ListView tem limitações: não rola horizontalmente, não tem grades irregulares, não tem animações de item.

**Solução 1 — Alternativas nativas do SDK (recomendado):**

| Necessidade | Alternativa nativa |
|---|---|
| Grade de fotos | `android.widget.GridView` |
| Rolagem horizontal | `HorizontalScrollView` + `LinearLayout` |
| Rolagem horizontal com estaques | `android.widget.HorizontalScrollView` + `Adapter` manual |
| Swipe to dismiss | `onTouchListener` + animação manual |
| Animações de item | `ViewPropertyAnimator` + `ViewAnimationUtils` |

**Solução 2 — Incluir RecyclerView comme JAR externo (quando realmente necessário):**

1. Baixar o AAR mais recente do RecyclerView do Maven Central
2. Extrair o `classes.jar` do AAR (AAR é ZIP):
   ```powershell
   # Renomear .aar → .zip e extrair
   Rename-Item recyclerview-1.3.2.aar recyclerview-1.3.2.zip
   Expand-Archive recyclerview-1.3.2.zip -DestinationPath recyclerview-lib
   # Copiar classes.jar para o projeto
   Copy-Item recyclerview-lib\classes.jar libs\recyclerview.jar
   ```
3. No `build.ps1`, adicionar o JAR ao classpath do javac e ao d8:
   ```powershell
   # No classpath do javac
   $EXTRA_JARS = "libs\recyclerview.jar"
   javac -cp "$PLATFORM;$EXTRA_JARS" -d "$BuildDir\classes" $srcFiles

   # Incluir no JAR e no d8
   jar cf "$BuildDir\classes.jar" -C "$BuildDir\classes" .
   # Extrair recyclerview classes para dentro do JAR também
   cd "$BuildDir\classes"
   jar xf "$pwd\..\..\libs\recyclerview.jar"
   cd "$pwd\..\.."
   # Agora compilar tudo com d8 (classes do app + recyclerview)
   jar cf "$BuildDir\classes.jar" -C "$BuildDir\classes" .
   ```
4. **Prós**: RecyclerView funcional. **Contras**: aumenta o tamanho do APK em ~200KB, precisa repetir o processo em cada atualização da lib.

### 12.2 ConstraintLayout

**Solução 1 — LinearLayout aninhado (sem dependências):**
```xml
<LinearLayout android:orientation="vertical">
    <LinearLayout android:orientation="horizontal">
        <View android:layout_weight="1" ... />
        <View android:layout_width="wrap_content" ... />
    </LinearLayout>
    <View android:layout_marginStart="..." ... />
</LinearLayout>
```
Com `layout_weight` + `layout_margin` + `gravity` cobre 100% dos casos que ConstraintLayout resolveria.

**Solução 2 — Incluir como JAR externo** (mesmo processo do RecyclerView):
- `implementation 'androidx.constraintlayout:constraintlayout:2.1.4'` → baixar AAR, extrair classes.jar, adicionar ao build.

### 12.3 CameraX / Camera2

Android tem duas APIs de câmera nativas que **não precisam de AndroidX**:

| API | Disponível desde | Status |
|---|---|---|
| `android.hardware.Camera` (Camera1) | API 1 | Deprecated desde API 21, mas funciona |
| `android.hardware.camera2` (Camera2) | API 21 (minSdk do projeto) | Ativa e recomendada |

**Pattern para Camera2 sem AndroidX:**

```java
public class CameraActivity extends Activity {
    private CameraDevice cameraDevice;
    private CameraManager cameraManager;
    private SurfaceView previewView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_camera);

        cameraManager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
        previewView = findViewById(R.id.previewView);

        findViewById(R.id.btnCapturar).setOnClickListener(v -> capturarFoto());
        abrirCamera();
    }

    private void abrirCamera() {
        try {
            String cameraId = cameraManager.getCameraIdList()[0]; // traseira
            cameraManager.openCamera(cameraId, new CameraDevice.StateCallback() {
                @Override
                public void onOpened(CameraDevice camera) {
                    cameraDevice = camera;
                    criarSessao();
                }
                @Override
                public void onDisconnected(CameraDevice camera) { camera.close(); }
                @Override
                public void onError(CameraDevice camera, int error) { camera.close(); }
            }, null);
        } catch (Exception e) {
            Log.e("Camera", "Erro ao abrir câmera", e);
        }
    }
}
```

**Limitação**: Camera2 é verbosa (~200 linhas para preview + captura). CameraX reduz isso para ~50 linhas, mas exige AndroidX. Para a abordagem manual, Camera2 é o caminho.

### 12.4 Firebase Cloud Messaging (FCM)

FCM depende de `com.google.android.gms:play-services-base` e `com.google.firebase:firebase-messaging`. Incorporar manualmente é complexo devido ao número de dependências transitivas.

**Alternativas sem Firebase:**

| Alternativa | Prós | Contras |
|---|---|---|
| WebSocket (OkHttp) | Total controle, sem Google Play | Precisa de servidor próprio, consome bateria |
| MQTT (Eclipse Paho) | Leve, protocolo padrão IoT | Precisa de broker MQTT |
| SMS Retriever API | Nativo, sem dependências | Só para SMS OTP |
| Polling HTTP periódico | Simples de implementar | Consome dados, não é tempo real |

**Fluxo WebSocket mínimo (sem dependências externas):**

```java
// Java tem java.net.WebSocket? Não. Mas pode usar java.net.Socket + HTTP upgrade manual.
// Ou incluir OkHttp como JAR externo (mesmo processo do RecyclerView).
```

Se FCM for estritamente necessário, o **caminho pragmático** é:
1. Criar um module separado com Gradle só para notificações
2. Incluir o AAR gerado como dependência no build manual
3. OU migrar o projeto para Gradle (AndroidX)

### 12.5 Fragments (navegação complexa)

Sem AndroidX, existe `android.app.Fragment` (nativo do framework). Ele funciona, mas é limitado:

| Funcionalidade | Fragment nativo | Fragment AndroidX |
|---|---|---|
| BackStack | `fragmentTransaction.addToBackStack()` | Mesmo |
| Animações | `setCustomAnimations()` | Mesmo |
| DialogFragment | Disponível | Disponível |
| ViewPager | Não disponível | ViewPager2 |
| Lifecycle coupling | Manual | Automático com LiveData |

**Alternativa sem Fragment:** ViewFlipper + pilha manual de estados:

```java
// Pilha de páginas
private Stack<Integer> pageHistory = new Stack<>();

private void navegarPara(int pageIndex) {
    pageHistory.push(currentPage);
    switchTab(pageIndex);
}

private void voltar() {
    if (!pageHistory.isEmpty()) {
        switchTab(pageHistory.pop());
    } else {
        finish();
    }
}

// Sobrescrever o botão voltar
@Override
public void onBackPressed() {
    if (!pageHistory.isEmpty()) {
        voltar();
    } else {
        super.onBackPressed();
    }
}
```

### 12.6 Mapas (Google Maps)

Google Maps SDK (`com.google.android.gms:play-services-maps`) é um AAR grande com várias dependências.

**Alternativa:** usar `WebView` com OpenStreetMap / Leaflet.js:
```java
WebView mapView = findViewById(R.id.mapView);
mapView.getSettings().setJavaScriptEnabled(true);
mapView.loadUrl("file:///android_asset/mapa.html");
```

O HTML carrega Leaflet.js do assets e mostra o mapa sem dependências externas.

### 12.7 Resumo — Matriz de Decisão

| Funcionalidade | Precisa de lib externa? | Solução nesta metodologia |
|---|---|---|
| Lista simples | Não | `ListView` + `BaseAdapter` |
| Grade de imagens | Não | `GridView` |
| Rolagem horizontal | Não | `HorizontalScrollView` |
| Lista complexa (animações, swipe) | Sim (RecyclerView) | Baixar JAR + incluir no build |
| Layout responsivo | Não | `LinearLayout` + `layout_weight` |
| Câmera | Não | `Camera2` (nativa, API 21+) |
| Notificações push | Sim (FCM) | WebSocket ou polling HTTP |
| Fragmentos | Não | `ViewFlipper` + pilha manual |
| Mapas | Sim (Google Maps) | `WebView` + Leaflet.js |
| Banco local relacional | Não | `SQLiteOpenHelper` (nativo) |
| Banco local NoSQL | Sim (Room) | Arquivos JSON + Gson manual |
| Gráficos | Sim (MPAndroidChart) | `Canvas` + `View.onDraw()` nativo |

A regra de ouro: **se o SDK nativo oferece, use. Se não oferece, avalie se uma alternativa nativa atende. Só inclua lib externa se for estritamente necessário.**

### 12.8 Pattern para incluir qualquer JAR externo

Quando nenhuma alternativa nativa serve, este é o pattern padrão para adicionar qualquer biblioteca:

```powershell
# 1. Criar pasta libs/
New-Item -ItemType Directory -Path libs -Force

# 2. Baixar o JAR (exemplo: OkHttp)
# curl -L -o libs/okhttp.jar https://repo1.maven.org/.../okhttp-4.12.0.jar

# 3. No build.ps1, adicionar ao classpath
$EXTRA_JARS = ""
Get-ChildItem libs -Filter "*.jar" | ForEach-Object {
    $EXTRA_JARS += ";$($_.FullName)"
}
$CLASSPATH = "$PLATFORM$EXTRA_JARS"

# 4. Compilar com classpath estendido
exec "Compile Java" "javac -cp `"$CLASSPATH`" -d `"$BuildDir\classes`" $srcFiles"

# 5. Extrair classes das libs para dentro do JAR do app (merge)
exec "Merge libs" "cd /d `"$FullBuildDir\classes`" &&"
foreach ($jar in (Get-ChildItem libs -Filter "*.jar")) {
    exec "Extract $jar" "cd /d `"$FullBuildDir\classes`" && jar xf `"$($jar.FullName)`""
}
# Isso faz com que d8 inclua tudo em um único classes.dex
```

---

> *Documentado em 13/07/2026 com base no desenvolvimento do Supermercado Caixa — uma calculadora de compras Android construída do zero com SDK puro.*
