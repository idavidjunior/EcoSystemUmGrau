param([string]$OutputName = "CellCleaner", [switch]$Release = $false)

$BuildDir = "build"
$ANDROID_HOME = $env:ANDROID_HOME
$BT = "$ANDROID_HOME\build-tools\36.0.0"
$PLATFORM = "$ANDROID_HOME\platforms\android-36\android.jar"
$FullBuildDir = "$pwd\$BuildDir"

if ($Release) {
    $KEYSTORE = "$pwd\release.keystore"
    $STOREPASS = "opencode"
    $KEYPASS = "opencode"
    $KEYALIAS = "cellcleaner"
} else {
    $KEYSTORE = "$env:USERPROFILE\.android\debug.keystore"
    $STOREPASS = "android"
    $KEYPASS = "android"
    $KEYALIAS = "androiddebugkey"
}

$Suffix = if ($Release) { "-release" } else { "-debug" }
$ApkName = "$OutputName$Suffix"

if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
New-Item -ItemType Directory -Path "$BuildDir\classes", "$BuildDir\dex" -Force | Out-Null

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
