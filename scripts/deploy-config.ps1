param(
    [string]$ConfigName = "full",
    [switch]$Rollback
)

$ErrorActionPreference = "Stop"
$opencode = "C:\Users\Playtec-bancada\AppData\Roaming\npm\opencode.cmd"
$configDir = "C:\Users\Playtec-bancada\.config\opencode"
$mainConfig = "$configDir\opencode.jsonc"
$backupConfig = "$configDir\opencode.jsonc.backup"

Write-Host "`n=== VOX UM GRAU - Deploy de Configuracao ===" -ForegroundColor Cyan

if ($Rollback) {
    Write-Host "[1/3] Rollback solicitado..." -ForegroundColor Yellow
    if (Test-Path $backupConfig) {
        Copy-Item $backupConfig $mainConfig -Force
        Write-Host "[2/3] Backup restaurado." -ForegroundColor Green
        Write-Host "[3/3] Testando config limpa..." -ForegroundColor Yellow
        & $opencode debug config --pure 2>&1 | Out-Null
        if ($?) {
            Write-Host "`n[OK] Config limpa validada. Rollback concluido." -ForegroundColor Green
        } else {
            Write-Host "[FALHA] Config limpa tambem falhou! Verifique manualmente." -ForegroundColor Red
        }
    } else {
        Write-Host "Nenhum backup encontrado em $backupConfig" -ForegroundColor Red
    }
    return
}

Write-Host "[1/5] Backup da config atual..." -ForegroundColor Yellow
Copy-Item $mainConfig $backupConfig -Force

Write-Host "[2/5] Aplicando config '$ConfigName'..." -ForegroundColor Yellow
$sourceFile = "$configDir\opencode.$ConfigName.jsonc"
if (-not (Test-Path $sourceFile)) {
    Write-Host "Arquivo nao encontrado: $sourceFile" -ForegroundColor Red
    Write-Host "Arquivos disponiveis:" -ForegroundColor Yellow
    Get-ChildItem "$configDir\opencode.*.jsonc" | Select-Object Name
    exit 1
}
Copy-Item $sourceFile $mainConfig -Force

Write-Host "[3/5] Testando config com 'opencode debug config'..." -ForegroundColor Yellow
$result = & $opencode debug config --pure 2>&1

if ($LASTEXITCODE -ne 0 -or $result -match "Error|error|Invalid|invalid") {
    Write-Host "`n[FALHA] Config INVALIDA! Erros encontrados:" -ForegroundColor Red
    $result | Select-String -Pattern "Error|Invalid|Missing|Expected" -SimpleMatch | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }

    Write-Host "`n[4/5] Rollback automatico..." -ForegroundColor Yellow
    Copy-Item $backupConfig $mainConfig -Force

    Write-Host "[5/5] Testando config original..." -ForegroundColor Yellow
    & $opencode debug config --pure 2>&1 | Out-Null
    if ($?) {
        Write-Host "[OK] Config original restaurada e funcionando." -ForegroundColor Green
    } else {
        Write-Host "[FALHA CRITICA] Config original tambem falhou!" -ForegroundColor Red
    }

    Write-Host "`nResumo: CONFIG REJEITADA - Rollback executado" -ForegroundColor Red
    Write-Host "Revise os erros acima e corrija antes de tentar novamente." -ForegroundColor Yellow
    exit 1
}

Write-Host "[4/5] Config VALIDA! Nenhum erro encontrado." -ForegroundColor Green

Write-Host "[5/5] Sedimentando config..." -ForegroundColor Yellow
Remove-Item $backupConfig -Force -ErrorAction SilentlyContinue

Write-Host "`n[OK] Config '$ConfigName' sedimentada com sucesso!" -ForegroundColor Green
Write-Host "A config foi testada e aprovada. Pode reiniciar o OpenCode." -ForegroundColor Cyan
