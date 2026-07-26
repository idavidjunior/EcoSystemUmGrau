$SdkDir = "C:\Users\Playtec-bancada\AppData\Local\Android\Sdk"
$BuildTools = "$SdkDir\build-tools\34.0.0"
$Platform = "$SdkDir\platforms\android-36\android.jar"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutDir = "$ProjectRoot\bin"
$GenDir = "$ProjectRoot\gen"
$ClassesDir = "$OutDir\classes"
$Aapt = "$BuildTools\aapt.exe"
$D8 = "$BuildTools\d8.bat"
$Apksigner = "$BuildTools\apksigner.bat"
$Zipalign = "$BuildTools\zipalign.exe"
$Javac = "javac"

$AppName = "BibliaEstudoCompleta"
$Keystore = "$ProjectRoot\debug.keystore"
$UnsignedApk = "$OutDir\$AppName.unsigned.apk"
$AlignedApk = "$OutDir\$AppName.aligned.apk"
$FinalApk = "$OutDir\$AppName.apk"

Write-Host "=== Building $AppName ===" -ForegroundColor Cyan

# Step 0: Clean
Write-Host "[1/7] Cleaning..." -ForegroundColor Yellow
if (Test-Path $OutDir) { Remove-Item -Recurse -Force "$OutDir\*" -ErrorAction SilentlyContinue }
if (Test-Path $GenDir) { Remove-Item -Recurse -Force "$GenDir\*" -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
New-Item -ItemType Directory -Path $ClassesDir -Force | Out-Null
New-Item -ItemType Directory -Path $GenDir -Force | Out-Null

# Step 1: Generate R.java
Write-Host "[2/7] Generating R.java..." -ForegroundColor Yellow
& $Aapt package -f -m -J $GenDir -S "$ProjectRoot\res" -M "$ProjectRoot\AndroidManifest.xml" -I $Platform
if ($LASTEXITCODE -ne 0) { Write-Host "AAPT failed!" -ForegroundColor Red; exit 1 }

# Step 2: Compile Java sources
Write-Host "[3/7] Compiling Java sources..." -ForegroundColor Yellow
$javaFiles = @(Get-ChildItem -Recurse -Path "$ProjectRoot\src", "$GenDir" -Filter "*.java" | Select-Object -ExpandProperty FullName)
Write-Host "  Found $($javaFiles.Count) Java files"
if ($javaFiles.Count -eq 0) { Write-Host "No Java files found!" -ForegroundColor Red; exit 1 }
& $Javac -d $ClassesDir -encoding "UTF-8" -cp "$Platform" $javaFiles
if ($LASTEXITCODE -ne 0) { Write-Host "Compilation failed!" -ForegroundColor Red; exit 1 }

# Step 3: Jar classes then DEX
Write-Host "[4/7] Creating classes jar..." -ForegroundColor Yellow
$ClassesJar = "$OutDir\classes.jar"
jar cf "$ClassesJar" -C "$ClassesDir" .
if ($LASTEXITCODE -ne 0) { Write-Host "JAR creation failed!" -ForegroundColor Red; exit 1 }
Write-Host "  JAR size: $((Get-Item $ClassesJar).Length / 1KB) KB"

Write-Host "[4b/7] Converting to DEX..." -ForegroundColor Yellow
& cmd /c "`"$D8`" --lib `"$Platform`" --output `"$OutDir`" `"$ClassesJar`"" 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "DEX generation failed!" -ForegroundColor Red; exit 1 }
if (-not (Test-Path "$OutDir\classes.dex")) { Write-Host "DEX file not found!" -ForegroundColor Red; exit 1 }
Write-Host "  DEX size: $((Get-Item "$OutDir\classes.dex").Length / 1KB) KB"

# Step 4: Package resources (without DEX yet)
Write-Host "[5/7] Packaging resources + assets..." -ForegroundColor Yellow
& $Aapt package -f -M "$ProjectRoot\AndroidManifest.xml" -S "$ProjectRoot\res" -A "$ProjectRoot\assets" -I $Platform -F $UnsignedApk
if ($LASTEXITCODE -ne 0) { Write-Host "AAPT package failed!" -ForegroundColor Red; exit 1 }

# Step 5: Manually add classes.dex to APK (aapt add uses relative path for internal name)
Write-Host "[5b/7] Adding DEX to APK..." -ForegroundColor Yellow
Push-Location $OutDir
& cmd /c "`"$Aapt`" add -f `"$UnsignedApk`" classes.dex" 2>&1
$addOk = $LASTEXITCODE -eq 0
Pop-Location
if (-not $addOk) { Write-Host "Add DEX failed!" -ForegroundColor Red; exit 1 }

# Step 6: Zipalign
Write-Host "[6/7] Aligning..." -ForegroundColor Yellow
& $Zipalign -f 4 $UnsignedApk $AlignedApk
if ($LASTEXITCODE -ne 0) { Write-Host "Zipalign failed!" -ForegroundColor Red; exit 1 }

# Step 7: Sign
Write-Host "[7/7] Signing..." -ForegroundColor Yellow
& $Apksigner sign --ks $Keystore --ks-pass pass:android --out $FinalApk $AlignedApk
if ($LASTEXITCODE -ne 0) { Write-Host "Signing failed!" -ForegroundColor Red; exit 1 }

# Verify
Write-Host "=== Verification ===" -ForegroundColor Cyan
& $Apksigner verify $FinalApk

$size = (Get-Item $FinalApk).Length
$sizeMB = [math]::Round($size/1MB, 1)
Write-Host "APK built: $FinalApk ($sizeMB MB)" -ForegroundColor Green
Write-Host "Icon: ic_launcher.png in drawable-*" -ForegroundColor Green
