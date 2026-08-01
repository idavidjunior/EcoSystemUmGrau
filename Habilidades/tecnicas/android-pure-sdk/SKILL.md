---
name: android-pure-sdk
description: Use ONLY when building Android apps with pure SDK (no AndroidX, no Gradle, no Kotlin). Covers aapt+javac+d8+apksigner build pipeline, tab-based navigation with FrameLayout, inline editing with ListView/BaseAdapter, custom numpad, JSON persistence, theme system, and all architecture patterns from the Supermercado Caixa project. Trigger keywords: "android pure sdk", "aapt", "d8", "apksigner", "no androidx", "no gradle", "build.ps1", "manual build android", "sdk puro".
---

# Android Pure SDK Development

## Core Principles

- **Zero external dependencies** — only `android.jar` from the target platform
- **Manual build** — `aapt` + `javac` + `jar` + `d8` + `zipalign` + `apksigner`
- **Fast iteration** — edit → build (`.\build.ps1`) → `adb install -r` → test
- **Backward compatibility** — minSdk 21, manual compatibility checks for API 23+ features

## Complete Build Pipeline Intelligence

This section documents the complete mental model of how Android builds work at the SDK level — not just what commands to run, but why each step exists, what can go wrong, and how to fix it.

### Environment Prerequisites

```powershell
$ANDROID_HOME = $env:ANDROID_HOME
# Must contain:
#   build-tools/36.0.0/   (aapt.exe, d8.bat, zipalign.exe, apksigner.bat)
#   platforms/android-36/  (android.jar)
#   cmdline-tools/latest/  (sdkmanager, d8.bat fallback)
# JDK 8+ must be on PATH  (javac, jar, keytool)
```

**Getting ANDROID_HOME right is the #1 build failure cause.** Common paths:
- `C:\Users\USER\AppData\Local\Android\Sdk`
- `C:\Android\Sdk`
- Set via environment variable or hardcode in build.ps1

### Step-by-Step Pipeline

#### Step 1: `aapt package` — Generate R.java

```powershell
aapt package -f -m -M AndroidManifest.xml -S res -I "%PLATFORM%" -J src
```

**What it does:** Parses all XML resources (layouts, drawables, strings, colors, styles), assigns each an integer ID, and writes `R.java` into the source tree.

**Flags:**
- `-f` — force overwrite
- `-m` — create package directory structure under `-J` target
- `-M` — path to AndroidManifest.xml
- `-S` — path to `res/` directory
- `-I` — android.jar platform (for built-in resource references like `@android:style/`)
- `-J` — where to write R.java (typically `src/` so it's on the javac source path)

**Why it's needed:** Java code references resources symbolically (`R.layout.activity_main`, `R.color.primary`). These are just integer constants. Without R.java, the code won't compile.

**What R.java contains:**
```java
public final class R {
    public static final class layout { public static final int activity_main = 0x7F030000; }
    public static final class id { public static final int cartList = 0x7F080000; }
    public static final class string { public static final int app_name = 0x7F0F0000; }
    public static final class color { public static final int primary = 0x7F050000; }
    // etc.
}
```

**Common errors:**
- `ERROR: No resource found that matches the given name` — a resource reference in XML is wrong
- `ERROR: Resource entry X already has entry` — duplicate resource ID
- **Missing R.java**: the javac step will fail with `cannot find symbol R`. Solution: check that `-J src` is correct and `src/` is on the javac source path.

**Important quirk:** `aapt` auto-generates `layout-v22` variants from `layout/` files even if no `layout-v22/` directory exists in source. This is a known aapt behavior — it creates shim layouts to support the `elevation` attribute. Don't be confused when you see these files in the APK.

#### Step 2: `javac` — Compile Java to Bytecode

```powershell
javac -cp "%PLATFORM%" -d "%BuildDir%\classes" %srcFiles%
```

**What it does:** Compiles all `.java` files (including generated `R.java`) into `.class` files (JVM bytecode).

**Flags:**
- `-cp` — classpath (android.jar for framework classes)
- `-d` — output directory for .class files
- Last argument is all source files (space-separated)

**Source file collection:**
```powershell
$srcFiles = (Get-ChildItem -Recurse -Path src -Filter "*.java" | ForEach-Object { $_.FullName }) -join " "
```
This must include ALL `.java` files including `R.java` in the `src/` tree.

**Classpath mental model:** The `-cp` tells javac where to find compiled classes that your code depends on. `android.jar` contains all framework classes: `Activity`, `View`, `ListView`, `AlertDialog`, etc. If you include external JARs (like RecyclerView), they must also be on the classpath.

**Common errors:**
- `error: cannot find symbol` — a class or method doesn't exist. Check: import statement, classpath, or API level mismatch (using API 30+ method when compiling against API 21)
- `error: package R does not exist` — aapt didn't generate R.java or it's not in the source path
- `warning: [deprecation]` — using deprecated API. Safe to ignore, can suppress with `-Xlint:-deprecation`
- `unmappable character for encoding ASCII` — file has non-ASCII characters. Add `-encoding UTF-8` to javac

**Why jar the classes?** `d8` (the dex compiler) takes a JAR as input, not loose .class files. So we package them first.

#### Step 3: `jar` — Package into JAR

```powershell
jar cf "%BuildDir%\classes.jar" -C "%BuildDir%\classes" .
```

**What it does:** Creates a standard Java JAR file containing all compiled .class files.

**Flags:**
- `c` — create
- `f` — output file
- `-C dir .` — change to directory and add everything

**Why:** d8 doesn't accept directory trees of .class files; it needs a JAR. This is a historical Android toolchain requirement.

#### Step 4: `d8` — Convert JVM Bytecode to Dalvik Bytecode

```powershell
d8 --lib "%PLATFORM%" --release --output "%BuildDir%\dex" "%BuildDir%\classes.jar"
```

**What it does:** Converts `.class` files (JVM bytecode) to `classes.dex` (Dalvik Executable format — Android's VM bytecode). This is the step where your Java becomes Android-runnable.

**Flags:**
- `--lib` — platform android.jar (for resolving framework references without including them)
- `--release` — optimize for release (smaller dex)
- `--output` — output directory (the `classes.dex` file will be written here)
- Last argument is the input JAR

**d8 vs dx (historical):** d8 replaced dx in Android 8.0 (2018). d8 is faster, produces smaller DEX, and is the only supported option for recent build-tools. The command-line tool is `d8.bat` on Windows.

**DEX format:** Unlike standard Java which has one `.class` per file, DEX packs ALL classes into a single `classes.dex` file. This is Android's optimization for mobile — one file to load, with cross-class reference optimization.

**Multi-dex:** If your app exceeds the 64K method reference limit, d8 produces multiple DEX files (`classes.dex`, `classes2.dex`, etc.). For most pure-SDK apps this is unnecessary.

**Common errors:**
- `Error: null, ClassNotFoundException` — a referenced class is missing from the classpath
- `Error: Cannot fit requested classes in a single dex file` — 64K method limit hit. Either reduce dependencies or enable multi-dex
- `Error: Type X is defined multiple times` — duplicate class in classpath (usually from including android.jar AND a library that contains the same class)

**Verification:** Check that `%BuildDir%\dex\classes.dex` exists after the command.

#### Step 5: `aapt package` — Build APK Skeleton

```powershell
aapt package -f -M AndroidManifest.xml -S res -I "%PLATFORM%" -F "%BuildDir%\%ApkName%-unsigned.apk"
```

**What it does:** Creates an APK file containing all compiled resources BUT not yet the DEX (no Java code yet). The APK at this stage is "unsigned" — it hasn't been signed for installation.

**Flags:**
- `-F` — output APK file path
- All other flags same as Step 1

**What's inside the APK at this point:**
```
META-INF/
res/          — compiled resources (binary XML, drawables, etc.)
AndroidManifest.xml  — compiled binary XML
resources.arsc       — compiled resource table (string pool, IDs, themes)
```
**No `classes.dex` yet** — we add it in the next step.

#### Step 6: `aapt add` — Inject DEX

```powershell
copy /Y dex\classes.dex classes.dex
aapt add %ApkName%-unsigned.apk classes.dex
```

**Mental model:** This is a UNIX `ar`-style archive operation. `aapt add` inserts the `classes.dex` file into the APK ZIP archive.

**Why not include DEX in Step 5?** The two-command pattern exists because `aapt package -F` creates the APK from scratch each time. If we had DEX available at that point, we could skip this step, but the DEX generation (d8) happens after resource packaging in most scripts because of tool ordering requirements.

**`copy /Y` inside the build dir:** The `aapt add` command requires the file being added to be in the current working directory. The `cd /d "%FullBuildDir%"` before the command is critical.

**Now the APK contains:**
```
META-INF/
res/
AndroidManifest.xml
resources.arsc
classes.dex   ← just added
```

#### Step 7: `zipalign` — Align for Performance

```powershell
zipalign -f -v 4 "%BuildDir%\%ApkName%-unsigned.apk" "%BuildDir%\%ApkName%-aligned.apk"
```

**What it does:** Reorganizes the APK ZIP entries so that all uncompressed data starts at 4-byte boundaries. This allows Android's `mmap()` to access file data directly without copying.

**Why 4-byte alignment:** ARM processors read memory more efficiently at aligned addresses. Critical for resource loading performance.

**Flags:**
- `-f` — force overwrite output
- `-v` — verbose (lists each file and alignment status)
- `4` — alignment in bytes

**What "OK" looks like:**
```
Verifying alignment of file.apk (4)...
  49 AndroidManifest.xml (OK - compressed)
  34757 classes.dex (OK - compressed)
Verification successful
```
Every line must say `(OK - ...)` or `(OK - compressed)`. If any file shows misalignment, zipalign fails.

**Why separate output file:** The `-f` flag overwrites the output file, but we keep the unsigned version as a backup.

**What happens if you skip zipalign:** On Android 11+, the package manager refuses to install the app with `INSTALL_FAILED_INVALID_APK`. On older versions, the app works but loads resources slightly slower.

#### Step 8: `apksigner` — Sign the APK

```powershell
apksigner sign --ks "%KEYSTORE%" --ks-pass pass:%STOREPASS% --key-pass pass:%KEYPASS% --ks-key-alias %KEYALIAS% "%BuildDir%\%ApkName%-aligned.apk"
```

**What it does:** Cryptographically signs the APK using a keystore (private key). Android requires ALL APKs to be signed before installation. Unsigned APKs cannot be installed.

**Two keystore modes:**

| Mode | Keystore | StorePass | KeyAlias | Purpose |
|------|----------|-----------|----------|---------|
| Debug | `~/.android/debug.keystore` | `android` | `androiddebugkey` | Development |
| Release | `release.keystore` (project-local) | User-defined | User-defined | Play Store |

**Debug keystore:** Created automatically by Android SDK when you first build. Same password/alias across all Android SDK installations. Never use for production.

**Release keystore creation:**
```powershell
keytool -genkey -v -keystore release.keystore -alias supermarket `
    -keyalg RSA -keysize 2048 -validity 10000 `
    -storepass opencode -keypass opencode `
    -dname "CN=AppName, OU=Developer, O=Company, L=City, ST=State, C=BR"
```

**⚠️ Release keystore is critical:** Without the SAME keystore, you CANNOT publish updates to an existing Play Store app. Store it in a secure, backed-up location.

**Verification:**
```powershell
apksigner verify APK.apk                                          # succeeds if valid
apksigner verify --print-certs APK.apk                             # shows certificate details
apksigner verify --print-certs APK.apk | Select-String "SHA-256"  # check cert fingerprint
```

### Complete build.ps1 Template

```powershell
param([string]$OutputName = "MyApp", [switch]$Release = $false)

$BuildDir = "build"
$ANDROID_HOME = $env:ANDROID_HOME
$BT = "$ANDROID_HOME\build-tools\36.0.0"
$PLATFORM = "$ANDROID_HOME\platforms\android-36\android.jar"
$FullBuildDir = "$pwd\$BuildDir"

if ($Release) {
    $KEYSTORE = "$pwd\release.keystore"
    $STOREPASS = "yourpass"
    $KEYPASS = "yourpass"
    $KEYALIAS = "youralias"
} else {
    $KEYSTORE = "$env:USERPROFILE\.android\debug.keystore"
    $STOREPASS = "android"
    $KEYPASS = "android"
    $KEYALIAS = "androiddebugkey"
}

$Suffix = if ($Release) { "-release" } else { "-debug" }
$ApkName = "$OutputName$Suffix"

# Clean and create directories
if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
New-Item -ItemType Directory -Path "$BuildDir\classes", "$BuildDir\dex" -Force | Out-Null

# Collect source files
$srcFiles = (Get-ChildItem -Recurse -Path src -Filter "*.java" | ForEach-Object { $_.FullName }) -join " "

function exec($desc, $cmd) {
    Write-Host $desc -ForegroundColor Cyan
    $out = cmd /c "$cmd 2>&1"
    if ($LASTEXITCODE -ne 0) { Write-Host $out -ForegroundColor Red; throw "$desc FAILED" }
    if ($out) { Write-Host $out }
}

exec "Generate R.java" "`"$BT\aapt.exe`" package -f -m -M AndroidManifest.xml -S res -I `"$PLATFORM`" -J src"
exec "Compile Java" "javac -encoding UTF-8 -cp `"$PLATFORM`" -d `"$BuildDir\classes`" $srcFiles"
exec "Create JAR" "jar cf `"$BuildDir\classes.jar`" -C `"$BuildDir\classes`" ."
exec "Convert to DEX" "`"$BT\d8.bat`" --lib `"$PLATFORM`" --release --output `"$BuildDir\dex`" `"$BuildDir\classes.jar`""
exec "Package APK" "`"$BT\aapt.exe`" package -f -M AndroidManifest.xml -S res -I `"$PLATFORM`" -F `"$BuildDir\$ApkName-unsigned.apk`""
exec "Add DEX to APK" "cd /d `"$FullBuildDir`" && copy /Y dex\classes.dex classes.dex >nul && `"$BT\aapt.exe`" add $ApkName-unsigned.apk classes.dex"
exec "Zipalign" "`"$BT\zipalign.exe`" -f -v 4 `"$BuildDir\$ApkName-unsigned.apk`" `"$BuildDir\$ApkName-aligned.apk`""
exec "Sign APK" "`"$BT\apksigner.bat`" sign --ks `"$KEYSTORE`" --ks-pass pass:$STOREPASS --key-pass pass:$KEYPASS --ks-key-alias $KEYALIAS `"$BuildDir\$ApkName-aligned.apk`""

Copy-Item "$BuildDir\$ApkName-aligned.apk" "$ApkName.apk" -Force
Write-Host "=== APK ready: $ApkName.apk ===" -ForegroundColor Green
```

### Common Build Errors — Root Cause and Fix

| Error | Step | Root Cause | Fix |
|-------|------|------------|-----|
| `cannot find symbol R` | javac | R.java not in source path | Check `-J src` in aapt, ensure R.java generated in src/ tree |
| `corrupted characters / acentos` | javac | Windows default encoding ≠ UTF-8 | Add `-encoding UTF-8` to javac command |
| `No resource found` in XML | aapt | Referenced string/drawable not defined | Add missing resource or fix reference |
| `mismatched tag` | aapt | XML has unclosed/extra tag | Check layout XML for balanced tags (use a decent editor) |
| `Unmatched >` / `>` | aapt | Wrong closing tag order | Common in nested LinearLayouts — trace each open/close |
| `ClassNotFoundException` | d8 | Missing class in classpath | Check javac classpath includes all dependencies |
| `INSTALL_FAILED_INVALID_APK` | install | Zipalign missing or failed | Check zipalign output, re-run |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | install | APK signed with different key | Same app must be signed with same keystore always |
| `Failure [INSTALL_FAILED_OLDER_SDK]` | install | targetSdkVersion < device OS | Update targetSdkVersion or use older device |
| No main activity found | install | Missing intent-filter in manifest | Add `<action android:name="android.intent.action.MAIN" />` |
| `Error while executing: am start` | install | Activity crash on launch | Check Logcat for crash details |
| `INSTALL_FAILED_NO_MATCHING_ABIS` | install | Native library architecture mismatch | Only relevant if using NDK native libs |
| `INVALID_SENDER` | install (split) | Split APK mismatch | Only relevant for app bundles |

### ADB Workflow

```powershell
# Connect WiFi device
adb tcpip 5555
adb connect 100.64.71.9:5555

# Install APK
adb -s 100.64.71.9:5555 install -r MyApp-debug.apk

# Force stop app
adb shell am force-stop com.yourdomain.yourapp

# Clear app data
adb shell pm clear com.yourdomain.yourapp

# View logs
adb logcat -s SuperCalc:* *:S

# View full logcat with grep filter (PowerShell)
adb logcat | Select-String "SuperCalc"

# Capture screenshot
adb shell screencap /sdcard/screen.png
adb pull /sdcard/screen.png

# List installed packages
adb shell pm list packages | Select-String "calculator"

# Uninstall
adb uninstall com.yourdomain.yourapp
```

### Dependency Inclusion Pattern

When a pure SDK project needs an external library (the LAST resort):

1. Create `libs/` directory
2. Download the JAR or extract `classes.jar` from AAR:
   ```powershell
   # AAR is just ZIP
   Rename-Item library.aar library.zip
   Expand-Archive library.zip -DestinationPath lib-extracted
   Copy-Item lib-extracted\classes.jar libs\library.jar
   ```
3. Modify build.ps1 to include the JAR:
   ```powershell
   $EXTRA_JARS = ""
   Get-ChildItem libs -Filter "*.jar" | ForEach-Object {
       $EXTRA_JARS += ";$($_.FullName)"
   }
   javac -cp "$PLATFORM$EXTRA_JARS" -d "$BuildDir\classes" $srcFiles
   ```
4. Extract library classes into the project JAR before d8:
   ```powershell
   cd "$FullBuildDir\classes"
   jar xf ..\..\libs\library.jar
   cd "$FullBuildDir\.."
   ```
5. Rebuild normally

## Project Structure
```
res/
  drawable/         — XML drawables (shapes, selectors, launcher icon)
  layout/           — activity_main.xml, item_row.xml
  values/           — strings.xml, colors.xml, styles.xml
  layout-v22/       — Same layouts with elevation (auto-generated by aapt)

src/com/yourdomain/yourapp/
  MainActivity.java
  adapter/YourAdapter.java
  models/YourModel.java
```

## AndroidManifest Essentials
```xml
<uses-sdk android:minSdkVersion="21" android:targetSdkVersion="36" />
<uses-permission android:name="android.permission.VIBRATE" />
<application android:theme="@style/AppTheme" android:debuggable="false">
    <activity android:name=".MainActivity" android:exported="true"
        android:windowSoftInputMode="adjustResize">
        <intent-filter>
            <action android:name="android.intent.action.MAIN" />
            <category android:name="android.intent.category.LAUNCHER" />
        </intent-filter>
    </activity>
</application>
```

## Tab Navigation Pattern

### XML Structure
```xml
<FrameLayout android:layout_width="match_parent"
    android:layout_height="0dp" android:layout_weight="1">
    <LinearLayout android:id="@+id/page0" android:visibility="visible" />
    <LinearLayout android:id="@+id/page1" android:visibility="gone" />
    <ScrollView  android:id="@+id/page2" android:visibility="gone" />
</FrameLayout>
```

### Java Switching
```java
private void switchTab(int index) {
    page0.setVisibility(index == 0 ? View.VISIBLE : View.GONE);
    page1.setVisibility(index == 1 ? View.VISIBLE : View.GONE);
    page2.setVisibility(index == 2 ? View.VISIBLE : View.GONE);

    tab0.setAlpha(index == 0 ? 1f : 0.6f);
    tab0.setBackgroundResource(index == 0 ? R.drawable.bg_tab_active : 0);
    // repeat for each tab

    if (index == 1) refreshPage1Data();
    if (index == 2) refreshPage2Data();
}
```

## Sub-tab Pattern (nested tabs)
Same technique within a tab page:
```java
private void switchSubTab(int index) {
    subPage0.setVisibility(index == 0 ? View.VISIBLE : View.GONE);
    subPage1.setVisibility(index == 1 ? View.VISIBLE : View.GONE);
    subTab0.setTextColor(index == 0 ? activeColor : inactiveColor);
    subTab0.setBackgroundResource(index == 0 ? R.drawable.bg_tab_active : 0);
}
```

## ListView + BaseAdapter Pattern

### Adapter Interface
```java
public interface YourListener {
    void onItemClick(int position);
    void onIncrement(int position);
    void onDecrement(int position);
    void onRemove(int position);
    void onNameChanged(int position, String name);
}
```

### Adapter Class
```java
public class YourAdapter extends BaseAdapter {
    private final Context context;
    private final List<YourModel> items;
    private final YourListener listener;
    private int editingPosition = -1;

    public void setEditingPosition(int pos) {
        if (editingPosition != pos) {
            int oldPos = editingPosition;
            editingPosition = pos;
            if (oldPos >= 0) notifyDataSetChanged();
            if (pos >= 0) notifyDataSetChanged();
        }
    }

    @Override public int getCount() { return items.size(); }
    @Override public Object getItem(int i) { return items.get(i); }
    @Override public long getItemId(int i) { return i; }
}
```

## Inline Editing Pattern

### XML Row Layout
Use `EditText` styled as label when not editing:
```xml
<EditText android:id="@+id/itemName"
    android:enabled="false"
    android:focusable="false"
    android:focusableInTouchMode="false"
    android:clickable="false"
    android:cursorVisible="false"
    android:background="@null" />
```

### getView() Toggle
```java
if (position == editingPosition) {
    nameEt.setEnabled(true);
    nameEt.setFocusable(true);
    nameEt.setFocusableInTouchMode(true);
    nameEt.setCursorVisible(true);
    nameEt.setBackgroundResource(R.drawable.bg_input);
    convertView.setBackgroundColor(highlightColor);
} else {
    nameEt.setEnabled(false);
    nameEt.setFocusable(false);
    nameEt.setCursorVisible(false);
    nameEt.setBackgroundResource(0);
    convertView.setBackgroundColor(position % 2 == 0 ? evenColor : oddColor);
}
```

### TextWatcher Management
```java
Object tag = editText.getTag();
if (tag instanceof TextWatcher) editText.removeTextChangedListener((TextWatcher) tag);

editText.setText(value);

TextWatcher watcher = new TextWatcher() {
    final int pos = position;
    @Override public void afterTextChanged(Editable s) {
        if (listener != null && pos == editingPosition) {
            listener.onNameChanged(pos, s.toString());
        }
    }
};
editText.addTextChangedListener(watcher);
editText.setTag(watcher);
```
**Always remove old watcher before `setText()`** to prevent infinite loop from `setText()` triggering the watcher.

## Custom Numpad Pattern

### Button Setup
```java
private void setupNumpad() {
    View.OnClickListener listener = v -> {
        String val = null;
        int id = v.getId();
        if (id == R.id.btnN0) val = "0";
        // ... map each button ID to its value
        if (val != null) handleNumpadInput(val);
    };
    // Register on all numpad buttons
    for (int id : new int[]{R.id.btnN0, R.id.btnN1, ..., R.id.btnN9}) {
        findViewById(id).setOnClickListener(listener);
    }
    // Operation buttons
    findViewById(R.id.btnOpAdd).setOnClickListener(v -> handleOperator("+"));
    findViewById(R.id.btnOpEq).setOnClickListener(v -> handleEquals());
}
```

### Input Buffer
```java
private StringBuilder priceBuffer = new StringBuilder();

private void handleNumpadInput(String val) {
    if (val.equals(",")) {
        if (priceBuffer.indexOf(",") == -1) priceBuffer.append(",");
    } else {
        priceBuffer.append(val);
    }
    updatePriceDisplay();
}

private void updatePriceDisplay() {
    if (priceBuffer.length() == 0) {
        priceDisplay.setText("R$ 0,00");
        return;
    }
    String raw = priceBuffer.toString().replace(",", "");
    while (raw.length() < 3) raw = "0" + raw;
    String formatted = raw.substring(0, raw.length() - 2) + "," + raw.substring(raw.length() - 2);
    // Remove leading zeros
    priceDisplay.setText("R$ " + formatted);
}
```

### Chained Operations
```java
private double operand1 = 0;
private String pendingOp = null;

private void handleOperator(String op) {
    if (pendingOp != null) {
        double current = getPriceFromDisplay();
        operand1 = evaluate(operand1, current, pendingOp);
    } else {
        operand1 = getPriceFromDisplay();
    }
    priceBuffer.setLength(0);
    pendingOp = op;
    updatePriceDisplay();
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

## JSON Persistence Pattern

### Market List Structure
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

### Expense Structure
```json
{
  "version": 1,
  "expenses": [
    {"description": "Conta de luz", "amount": 150.00, "category": "Luz", "date": 1721234567890}
  ]
}
```

### Save/Load Pattern
```java
private File getDataDir() {
    File base = getExternalFilesDir(null);
    if (base == null) base = getFilesDir();
    File dir = new File(base, "data_dir");
    if (!dir.exists()) dir.mkdirs();
    return dir;
}

private void saveToFile() {
    try {
        JSONObject root = new JSONObject();
        JSONArray arr = new JSONArray();
        for (Item i : items) {
            JSONObject obj = new JSONObject();
            obj.put("name", i.getName());
            // ... add fields
            arr.put(obj);
        }
        root.put("items", arr);
        FileWriter fw = new FileWriter(new File(getDataDir(), "data.json"));
        fw.write(root.toString(2));
        fw.close();
    } catch (Exception e) {
        Log.e("Tag", "Error saving", e);
    }
}

private void loadFromFile() {
    File file = new File(getDataDir(), "data.json");
    if (!file.exists()) return;
    try {
        BufferedReader br = new BufferedReader(new FileReader(file));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = br.readLine()) != null) sb.append(line);
        br.close();
        JSONObject root = new JSONObject(sb.toString());
        JSONArray arr = root.getJSONArray("items");
        items.clear();
        for (int i = 0; i < arr.length(); i++) {
            JSONObject obj = arr.getJSONObject(i);
            items.add(new Item(obj.getString("name"), ...));
        }
        adapter.notifyDataSetChanged();
    } catch (Exception e) {
        Log.e("Tag", "Error loading", e);
    }
}
```

## Theme System Pattern

```java
private static final int THEME_DEFAULT = 0;
private static final int THEME_DARK = 1;
private static final int THEME_BLUE = 2;

private void applyTheme() {
    switch (currentTheme) {
        case THEME_DARK:
            rootLayout.setBackgroundColor(darkBg);
            headerBar.setBackgroundColor(Color.parseColor("#1a1a1a"));
            break;
        case THEME_BLUE:
            rootLayout.setBackgroundColor(background);
            headerBar.setBackgroundColor(blueDark);
            break;
        default: // THEME_DEFAULT
            rootLayout.setBackgroundColor(background);
            headerBar.setBackgroundColor(headerBg);
            break;
    }
}
```

## Button Visibility Pattern (maintain grid)
```java
private void setButtonHidden(Button btn, boolean hidden) {
    btn.setVisibility(View.VISIBLE);
    btn.setAlpha(hidden ? 0f : 1f);
    btn.setEnabled(!hidden);
    btn.setClickable(!hidden);
}
```
Use instead of `setVisibility(GONE)` to keep layout alignment.

## Dual-mode Dialog Pattern
```java
private void showSelectionDialog() {
    final boolean[] isMultiSelect = {false};
    final Set<String> selectedItems = new HashSet<>();

    AlertDialog dialog = new AlertDialog.Builder(this)
        .setTitle("Selecionar")
        .setAdapter(adapter, null)  // null click listener — we set it on ListView
        .setPositiveButton("Aplicar", (d, w) -> { /* apply multi-selection */ })
        .setNegativeButton("Cancelar", null)
        .create();
    dialog.show();

    ListView listView = dialog.getListView();
    listView.setOnItemClickListener((parent, view, position, id) -> {
        if (isMultiSelect[0]) {
            // Toggle selection
        } else {
            // Single tap — action immediately
            dialog.dismiss();
        }
    });
    listView.setOnItemLongClickListener((parent, view, position, id) -> {
        isMultiSelect[0] = true;
        // Enter multi-select mode
        return true;
    });
}
```
The `isMultiSelect[0]` (single-element array) pattern is required because the flag is accessed from anonymous inner classes, which require effectively-final variables.

## Naming Conventions

- **Views:** camelCase (productNameInput, priceDisplay, cartList)
- **Methods:** camelCase with verb prefix (setupNumpad, addOrUpdateItem, loadFromFile)
- **Constants:** UPPER_SNAKE_CASE with prefix (KEY_THEME, KEY_SKIN)
- **XML IDs:** camelCase with type suffix (btnN0, productNameInput, cartList)

## Backward Compatibility

```java
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
    view.setBackgroundColor(context.getColor(R.color.name));
} else {
    view.setBackgroundColor(context.getResources().getColor(R.color.name));
}
```

## Vibration Pattern
```java
Vibrator v = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
if (v == null || !v.hasVibrator()) return;
long[] pattern = {0, 400, 100, 400};
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
    v.vibrate(VibrationEffect.createWaveform(pattern, -1));
} else {
    v.vibrate(pattern, -1);
}
```

## SharedPreferences Pattern (immediate save)
```java
private static final String PREFS_NAME = "settings";

// Save immediately on change
chkOption.setOnCheckedChangeListener((b, checked) -> {
    configValue = checked;
    prefs.edit().putBoolean("key", configValue).apply();
    applyConfig();
});

// Load on init
private void loadSettings() {
    configValue = prefs.getBoolean("key", defaultValue);
}
```

## Form Starts Empty Pattern

**Principle:** Every input form (calculator, expense CRUD) starts empty — no auto-loading from file on tab switch. The user must explicitly load saved data via file browser "Editar" button.

### Why
- User expects a blank slate when entering a form tab, consistent with "new calculation" mental model
- Forms are for CREATING new data; file browsers are for VIEWING saved data
- Separation of concerns: Tab 0/2 = input forms, Tab 1 = file browsers

### Implementation
```java
// switchTab() — do NOT auto-load on form tabs
if (index == 2) {
    refreshExpenseTotal();
    // DO NOT call loadExpensesFromFile() here
}

// Only load from file on explicit user action (Editar button)
loadBtn.setOnClickListener(view -> {
    loadExpensesFromFile(f);  // pass the specific File, not default
    switchTab(2);
});
```

### loadFromFile() should accept a File parameter
```java
private void loadFromFile() {
    loadFromFile(new File(getDataDir(), "default.json"));
}

private void loadFromFile(File file) {
    if (!file.exists()) return;
    // parse and populate...
}
```
This allows loading any file, not just the default one.

## "Limpar" Button — Screen Only, Not File

**Rule:** A "Limpar" button in a form/reset area should clear ONLY the in-memory state and UI, NEVER touch the saved file.

### Wrong (destructive):
```java
expenseItems.clear();
saveExpensesToFile();  // ❌ writes empty data to file!
```

### Correct (safe):
```java
expenseItems.clear();
adapter.notifyDataSetChanged();
refreshTotal();
// No saveToFile() — file remains intact
Toast.makeText(this, "Tela limpa. Dados salvos permanecem intactos.", Toast.LENGTH_SHORT).show();
```

### Rationale
- User expects "Limpar" = reset form for fresh input, not delete saved data
- If saving is needed, user presses "Salvar" explicitly
- Prevents accidental data loss: a form clear should never cascade to persistent storage

## File Browser "Editar" Must Pass Specific File

### Bug pattern
```java
// ❌ Always loads default file, ignores which file user tapped
loadBtn.setOnClickListener(view -> {
    loadFromFile();  // always loads "default.json"
    switchTab(2);
});
```

### Correct
```java
// ✅ Loads the SPECIFIC file the user selected
loadBtn.setOnClickListener(view -> {
    loadFromFile(f);  // f = the File from the adapter position
    switchTab(2);
});
```

The `f` variable must be effectively final (method parameter or local variable not reassigned).

## "Salvar" Creates New File, Not Overwrite

**Rule:** The "Salvar" button in expense forms must create a NEW timestamped file, never overwrite an existing saved file.

### Bug pattern
```java
// ❌ Always overwrites despesas.json
private void showSaveExpenseDialog() {
    saveExpensesToFile();  // writes to despesas.json — overwrites!
}
```

### Correct
```java
// ✅ Saves to despesas_YYYY-MM-DD_HH-mm-ss.json (new file each time)
private void showSaveExpenseDialog() {
    // Show title input dialog, then:
    saveExpensesToTimestampedFile(title);
}

private void saveExpensesToTimestampedFile(String title) {
    String timestamp = new SimpleDateFormat("yyyy-MM-dd_HH-mm-ss", ...).format(new Date());
    File file = new File(dir, "despesas_" + timestamp + ".json");
    root.put("title", title);
    root.put("date", timestamp);
    // write JSON to file
}
```

### Title on Save
The "Salvar" dialog must prompt for a title (pre-filled with date). The title is stored in the JSON `"title"` field:
- Displayed in file browser instead of raw filename
- Displayed in content preview dialog title
- Editable via "Renomear" button in content preview

### Keep `saveExpensesToFile()` for auto-save only
- `saveExpensesToFile()` (writes to `despesas.json`) is used for **inline editing auto-save** — quick saves while user is typing
- `saveExpensesToTimestampedFile()` is used for **explicit "Salvar" button** — user wants a permanent snapshot

## Key Design Decisions

1. **Single Activity** — Pages managed via visibility in FrameLayout; no Fragments needed for up to 5 screens
2. **ListView over RecyclerView** — Simpler API, sufficient for lists under 100 items with static layouts
3. **JSON files over SQLite** — Human-readable, editable outside app, no schema migrations
4. **StringBuilder for price** — Fine-grained control over display format, avoids floating-point display issues
5. **Numpad programmatically** — Listeners in Java rather than XML onClick for theme/skin flexibility
6. **Merge by name** — If name matches existing item, increment quantity instead of duplicating; NEVER merge unnamed items
7. **`setAlpha(0)` over `setVisibility(GONE)`** — Preserves grid layout in numpad
8. **`apply()` over `commit()`** — Asynchronous write, returns immediately (sufficient for small configs)
9. **Form Starts Empty** — Input forms never auto-load from file; user loads explicitly via file browser
10. **Limpar = screen only** — Clear button resets form without touching persistent storage
11. **Salvar = new file** — Explicit save creates timestamped snapshot, never overwrites existing saved files
12. **Title on save** — Save dialogs prompt for a title, stored in JSON `"title"` field for display in file browser
13. **`-encoding UTF-8` in javac** — Required on Windows to prevent corrupted Portuguese characters (ç, ã, é, etc.)

## Getting Started

### Files to create for a new project:
```
build.ps1
AndroidManifest.xml
res/values/strings.xml
res/values/colors.xml
res/values/styles.xml
res/layout/activity_main.xml
src/com/yourdomain/yourapp/MainActivity.java
```

### First build cycle:
1. Create directory structure
2. Write build.ps1 + AndroidManifest + basic layout + activity
3. Run `.\build.ps1` until it succeeds
4. `adb install -r` and verify on device
5. Iterate: feature → build → install → test → fix
