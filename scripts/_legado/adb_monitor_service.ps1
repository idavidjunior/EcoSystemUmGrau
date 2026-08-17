<# 
.SYNOPSIS
    Inicia o monitor ADB vivo como job em background

.DESCRIPTION
    Roda adb_monitor.py como job PowerShell persistente.
    Reinicia automaticamente se o job morrer.
    Logs em: $env:TEMP\adb_monitor.log

.USO
    .\adb_monitor_service.ps1 -Start
    .\adb_monitor_service.ps1 -Stop
    .\adb_monitor_service.ps1 -Status
    .\adb_monitor_service.ps1 -Restart
#>

param(
    [ValidateSet('Start','Stop','Status','Restart','Logs')]
    [string]$Action = 'Start',
    [int]$Interval = 30,
    [string]$LogFile = "$env:TEMP\adb_monitor.log"
)

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "adb_monitor_silent.py"
$python = "python"

function Start-Monitor {
    $jobName = "ADB_Monitor"
    
    # Verifica se já está rodando
    $existing = Get-Job -Name $jobName -ErrorAction SilentlyContinue
    if ($existing -and $existing.State -eq 'Running') {
        Write-Host "[INFO] Monitor já está rodando (Job ID: $($existing.Id))" -ForegroundColor Yellow
        return
    }
    
    # Remove jobs mortos
    Get-Job -Name $jobName -ErrorAction SilentlyContinue | Where-Object { $_.State -ne 'Running' } | Remove-Job -Force
    
    $scriptBlock = {
        param($py, $script, $interval, $logFile)
        $proc = Start-Process -FilePath $py -ArgumentList $script, "--interval", $interval -NoNewWindow -PassThru -RedirectStandardOutput $logFile -RedirectStandardError $logFile
        Wait-Process -Id $proc.Id
    }
    
    $job = Start-Job -Name $jobName -ScriptBlock $scriptBlock -ArgumentList $python, $scriptPath, $Interval, $LogFile
    Write-Host "[OK] Monitor ADB iniciado (Job ID: $($job.Id), Interval: ${Interval}s)" -ForegroundColor Green
    Write-Host "Logs: $LogFile" -ForegroundColor Cyan
    Write-Host "Comandos: Get-Job -Name ADB_Monitor | Receive-Job" -ForegroundColor DarkGray
}

function Stop-Monitor {
    $jobName = "ADB_Monitor"
    $jobs = Get-Job -Name $jobName -ErrorAction SilentlyContinue
    if ($jobs) {
        $jobs | Stop-Job -Force
        $jobs | Remove-Job -Force
        Write-Host "[OK] Monitor ADB parado" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Monitor não estava rodando" -ForegroundColor Yellow
    }
}

function Status-Monitor {
    $jobName = "ADB_Monitor"
    $job = Get-Job -Name $jobName -ErrorAction SilentlyContinue
    if ($job) {
        Write-Host "Status: $($job.State)" -ForegroundColor Cyan
        Write-Host "Job ID: $($job.Id)" -ForegroundColor Cyan
        if ($job.State -eq 'Running') {
            Write-Host "Rodando desde: $($job.PSBeginTime)" -ForegroundColor Green
        }
    } else {
        Write-Host "Status: PARADO (nenhum job encontrado)" -ForegroundColor Red
    }
}

function Logs-Monitor {
    if (Test-Path $LogFile) {
        Get-Content $LogFile -Tail 50 -Wait
    } else {
        Write-Host "[INFO] Log não existe ainda: $LogFile" -ForegroundColor Yellow
    }
}

switch ($Action) {
    'Start'     { Start-Monitor }
    'Stop'      { Stop-Monitor }
    'Status'    { Status-Monitor }
    'Restart'   { Stop-Monitor; Start-Sleep 1; Start-Monitor }
    'Logs'      { Logs-Monitor }
}