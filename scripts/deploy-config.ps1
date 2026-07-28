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
    Write-Host "[1/3] Rollback..." -ForegroundColor Yellow
    if (Test-Path $backupConfig) {
        Copy-Item $backupConfig $mainConfig -Force
        Write-Host "[2/3] Backup restaurado." -ForegroundColor Green
        Write-Host "[3/3] Testando..." -ForegroundColor Yellow
        $j = Start-Job -ScriptBlock { param($o) & $o serve --hostname 127.0.0.1 --port 4099 --pure 2>&1 } -ArgumentList $opencode
        Start-Sleep 3
        $err = Receive-Job -Job $j -ErrorAction SilentlyContinue
        Stop-Job $j -ErrorAction SilentlyContinue; Remove-Job $j -ErrorAction SilentlyContinue
        if ($err -match "Error|Invalid|Missing key") {
            Write-Host "[FALHA] $err" -ForegroundColor Red
        } else {
            Write-Host "[OK] Rollback concluido." -ForegroundColor Green
        }
    } else {
        Write-Host "Nenhum backup." -ForegroundColor Red
    }
    return
}

Write-Host "[1/5] Backup da config atual..." -ForegroundColor Yellow
Copy-Item $mainConfig $backupConfig -Force

Write-Host "[2/5] Aplicando config '$ConfigName'..." -ForegroundColor Yellow
$sourceFile = "$configDir\opencode.$ConfigName.jsonc"
if (-not (Test-Path $sourceFile)) {
    Write-Host "ERRO: $sourceFile nao encontrado." -ForegroundColor Red
    Write-Host "Disponiveis:"; Get-ChildItem "$configDir\opencode.*.jsonc" | Select-Object Name
    exit 1
}
Copy-Item $sourceFile $mainConfig -Force

Write-Host "[3/5] Teste 1 - 'opencode debug config'..." -ForegroundColor Yellow
$result = & $opencode debug config --pure 2>&1 | Out-String
if ($result -match "Error") {
    Write-Host "[FALHA] Config invalida!" -ForegroundColor Red
    $result | Select-String -Pattern "Error|Invalid|Missing" | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    Copy-Item $backupConfig $mainConfig -Force
    Write-Host "[ROLLBACK] Executado." -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] Schema valido." -ForegroundColor Green

Write-Host "[4/5] Teste 2 - 'opencode serve' (carrega MCP)..." -ForegroundColor Yellow
$port = 4099
$job = Start-Job -ScriptBlock { param($o, $p) & $o serve --hostname 127.0.0.1 --port $p 2>&1 } -ArgumentList $opencode, $port
Start-Sleep 4
$output = Receive-Job -Job $job -ErrorAction SilentlyContinue 2>&1 | Out-String
$listening = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue

if ($listening) {
    Stop-Job $job -ErrorAction SilentlyContinue; Remove-Job $job -ErrorAction SilentlyContinue
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Servidor iniciou sem erros. MCP carregado." -ForegroundColor Green
} else {
    Stop-Job $job -ErrorAction SilentlyContinue; Remove-Job $job -ErrorAction SilentlyContinue
    Write-Host "[FALHA] Servidor nao iniciou!" -ForegroundColor Red
    if ($output -match "Error") {
        $output | Select-String -Pattern "Error|Invalid|Missing" | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    }
    Write-Host "[ROLLBACK] Restaurando config limpa..." -ForegroundColor Yellow
    Copy-Item $backupConfig $mainConfig -Force
    exit 1
}

Write-Host "[5/5] Sedimentando config '$ConfigName'..." -ForegroundColor Yellow
Remove-Item $backupConfig -Force -ErrorAction SilentlyContinue

Write-Host "`n[OK] Config '$ConfigName' APROVADA e sedimentada!" -ForegroundColor Green
Write-Host "Passou nos 2 testes: schema valido + servidor iniciou." -ForegroundColor Cyan
