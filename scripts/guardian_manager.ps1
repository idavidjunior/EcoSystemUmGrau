param(
    [ValidateSet("start","stop","restart","status")]
    [string]$Action = "status"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$GuardianPy = Join-Path $ScriptDir "system_guardian.py"
$PidFile = Join-Path $ScriptDir "guardian.pid"
$StateFile = Join-Path $ScriptDir "guardian_state.json"
$LogFile = Join-Path $ScriptDir "guardian_log.txt"

function Write-Status { param($Msg) Write-Host "[Guardian] $Msg" }

switch ($Action) {
    "start" {
        if (Test-Path $PidFile) {
            $gpid = Get-Content $PidFile
            $proc = Get-Process -Id $gpid -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Status "Ja rodando (PID $gpid)"
                exit 0
            }
            Remove-Item $PidFile -Force
        }
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = "python"
        $psi.Arguments = "-u `"$GuardianPy`""
        $psi.WorkingDirectory = $ScriptDir
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.CreateNoWindow = $true
        $p = [System.Diagnostics.Process]::Start($psi)
        Start-Sleep -Seconds 2
        if (Test-Path $PidFile) {
            $newPid = Get-Content $PidFile
            Write-Status "Iniciado (PID $newPid)"
        } else {
            Write-Status "Falha ao iniciar"
        }
    }
    "stop" {
        if (Test-Path $PidFile) {
            $gpid = Get-Content $PidFile
            $proc = Get-Process -Id $gpid -ErrorAction SilentlyContinue
            if ($proc) {
                Stop-Process -Id $gpid -Force
                Write-Status "Parado (PID $gpid)"
            }
            Remove-Item $PidFile -Force
        } else {
            $procs = Get-Process -Name python -ErrorAction SilentlyContinue |
                Where-Object { (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine -like "*system_guardian*" }
            if ($procs) {
                $procs | Stop-Process -Force
                Write-Status "Parado ($($procs.Count) processo(s))"
            } else {
                Write-Status "Nao rodando"
            }
        }
    }
    "restart" {
        & $MyInvocation.MyCommand.Path -Action stop
        Start-Sleep -Seconds 1
        & $MyInvocation.MyCommand.Path -Action start
    }
    "status" {
        $running = $false
        if (Test-Path $PidFile) {
            $gpid = Get-Content $PidFile
            $proc = Get-Process -Id $gpid -ErrorAction SilentlyContinue
            if ($proc) {
                $running = $true
                $memMB = [math]::Round($proc.WorkingSet64 / 1MB, 1)
                Write-Status "Rodando (PID $gpid, ${memMB} MB)"
            }
        }
        if (-not $running) {
            $procs = Get-Process -Name python -ErrorAction SilentlyContinue |
                Where-Object { (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine -like "*system_guardian*" }
            if ($procs) {
                Write-Status "Rodando sem pid file ($($procs.Count) processo(s))"
                $running = $true
            }
        }
        if (-not $running) { Write-Status "Parado" }
        if (Test-Path $StateFile) {
            $state = Get-Content $StateFile | ConvertFrom-Json
            Write-Status "Ultimo estado: RAM $($state.ram_mb) MB livre, disco $($state.disk_gb) GB, nivel $($state.status)"
            if ($state.actions.Count -gt 0) {
                foreach ($a in $state.actions) {
                    if ($a.pid) { Write-Status "  Acao: matou PID $($a.pid) ($($a.name)) - $($a.mem_mb) MB" }
                    else { Write-Status "  Acao: $($a.note)" }
                }
            }
        }
        if (Test-Path $LogFile) {
            $lines = Get-Content $LogFile -Tail 5
            Write-Status "Ultimas linhas do log:"
            $lines | ForEach-Object { Write-Host "  $_" }
        }
    }
}
