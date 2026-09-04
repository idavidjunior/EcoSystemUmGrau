$scriptPath = Join-Path $PSScriptRoot 'start_tailscale_svc.ps1'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`""
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

try {
    Unregister-ScheduledTask -TaskName 'StartTailscale' -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName 'StartTailscale' -Action $action -Settings $settings -RunLevel Highest -Force
    Write-Host "Tarefa criada com sucesso" -ForegroundColor Green
    Start-Sleep 2
    Start-ScheduledTask -TaskName 'StartTailscale'
    Write-Host "Tarefa executada" -ForegroundColor Green
} catch {
    Write-Host "ERRO: $($_.Exception.Message)" -ForegroundColor Red
}

Start-Sleep 8
Write-Host ""
Write-Host "Estado dos servicos:" -ForegroundColor Cyan
Get-Service WinHttpAutoProxySvc,iphlpsvc,Tailscale -ErrorAction SilentlyContinue | Format-Table Name,Status,StartType -AutoSize
Write-Host ""
Write-Host "Tailscale status:" -ForegroundColor Cyan
& "C:\Program Files\Tailscale\tailscale.exe" status 2>&1
