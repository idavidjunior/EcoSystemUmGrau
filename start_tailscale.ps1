#requires -RunAsAdministrator
# Arranca Tailscale e servicos dependentes

Write-Host "Arrancando servicos Tailscale..." -ForegroundColor Cyan

$Services = @("WinHttpAutoProxySvc","iphlpsvc","Dnscache","netprofm")

foreach ($SvcName in $Services) {
    $Svc = Get-Service -Name $SvcName -ErrorAction SilentlyContinue
    if (-not $Svc) { Write-Host "  $SvcName: nao encontrado" -ForegroundColor Yellow; continue }

    if ($Svc.Status -eq "Running") {
        Write-Host "  $($Svc.Name): ja a correr" -ForegroundColor Green
    } else {
        try {
            if ($Svc.StartType -eq "Disabled") {
                Set-Service -Name $SvcName -StartupType Automatic -ErrorAction Stop
                Write-Host "  $($Svc.Name): startType alterado para Automatic" -ForegroundColor Yellow
            }
            Start-Service -Name $SvcName -ErrorAction Stop
            Write-Host "  $($Svc.Name): arrancado com sucesso" -ForegroundColor Green
        } catch {
            Write-Host "  $($Svc.Name): FALHA - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "Arrancando servico Tailscale..." -ForegroundColor Cyan

$Ts = Get-Service -Name "Tailscale" -ErrorAction SilentlyContinue
if ($Ts) {
    if ($Ts.Status -eq "Running") {
        Write-Host "  Tailscale: ja a correr" -ForegroundColor Green
    } else {
        try {
            Start-Service -Name "Tailscale" -ErrorAction Stop
            Write-Host "  Tailscale: arrancado com sucesso" -ForegroundColor Green
        } catch {
            Write-Host "  Tailscale: FALHA - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "Verificando estado final..." -ForegroundColor Cyan
Get-Service WinHttpAutoProxySvc,iphlpsvc,Dnscache,netprofm,Tailscale -ErrorAction SilentlyContinue |
    Format-Table Name,Status,StartType -AutoSize

Write-Host ""
Write-Host "Verificando tailscale status..." -ForegroundColor Cyan
& "C:\Program Files\Tailscale\tailscale.exe" status 2>&1

Write-Host ""
Read-Host "Pressione ENTER para fechar"
