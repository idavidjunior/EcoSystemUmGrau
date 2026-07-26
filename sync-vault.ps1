<#
.SYNOPSIS
    Sincroniza o vault do Obsidian (Desktop\Codigos) para dentro do repositorio (vault/).
    Deve ser executado ANTES de cada commit para manter o vault versionado.

.DESCRIPTION
    Copia apenas notas, codigo fonte e documentos (exclui builds, APKs, caches).
    Uso ideal: configurar como pre-commit hook ou executar manualmente antes de commitar.

.PARAMETER VaultSource
    Onde esta o vault Obsidian (default: ~/Desktop/Codigos)
.PARAMETER VaultDest
    Onde copiar no repositorio (default: <repo>/vault)
#>

param(
    [string]$VaultSource = "$env:USERPROFILE\Desktop\Codigos",
    [string]$VaultDest = ""
)

# Auto-detect repo root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $VaultDest) {
    $VaultDest = "$scriptDir\vault"
}

Write-Host "=== SYNC VAULT ===" -ForegroundColor Cyan
Write-Host "  De:  $VaultSource"
Write-Host "  Para: $VaultDest"

if (-not (Test-Path $VaultSource)) {
    Write-Host "[ERRO] Vault source nao encontrado: $VaultSource" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $VaultDest)) {
    Write-Host "[ERRO] Vault dest nao encontrado: $VaultDest" -ForegroundColor Red
    exit 1
}

# Exclude dirs (build artifacts, caches, binaries)
$excludeDirs = @(
    "build", ".cxx", ".gradle", ".gradle_temp", "build_output",
    "Reprodutor MP3 player", "bin", "obj",
    "__pycache__", ".pytest_cache", "node_modules",
    ".git"
)

# Build robocopy exclude args
$excludeArgs = $excludeDirs | ForEach-Object { "/xd", $_ }

# Sync using robocopy (mirror)
Write-Host "`nCopiando arquivos..." -ForegroundColor Cyan
$robocopyArgs = @(
    "`"$VaultSource`"",
    "`"$VaultDest`"",
    "/MIR",
    "/NDL",
    "/NFL",
    "/NJH",
    "/NJS",
    "/R:0",
    "/W:0"
) + $excludeDirs | ForEach-Object { @("/xd", "`"$_`"") } | ForEach-Object { $_ }

# Robocopy via cmd /c for proper quoting
$cmd = "robocopy `"$VaultSource`" `"$VaultDest`" /MIR /NDL /NFL /NJH /NJS /R:0 /W:0"
foreach ($ed in $excludeDirs) {
    $cmd += " /xd `"$ed`""
}
# Also exclude file types
$cmd += " /xf `"*.apk`" `"*.aab`" `"*.zip`" `"*.jar`" `"*.dex`" `"*.class`" `"*.keystore`" `"*.db`""

cmd /c $cmd 2>&1 | Out-Null

# Count after sync
$final = Get-ChildItem $VaultDest -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne ".gitignore" }
$finalSize = ($final | Measure-Object -Property Length -Sum).Sum

Write-Host "`n=== SYNC CONCLUIDO ===" -ForegroundColor Green
Write-Host "  Arquivos: $($final.Count)"
Write-Host "  Tamanho: $('{0:N2}' -f ($finalSize / 1MB)) MB"
Write-Host "`nAgora execute git add vault/ && git commit para versionar as notas."
exit 0
