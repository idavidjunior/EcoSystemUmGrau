param(
    [int]$Interval = 20,
    [string]$BridgePort = "8765",
    [string]$LogPath = "$env:USERPROFILE\Desktop\Codigos\EcoSystemUmGrau\scripts\watchdog_log.txt"
)

$ErrorActionPreference = "SilentlyContinue"
$log = [System.IO.StreamWriter]::new($LogPath, $true)
$log.AutoFlush = $true

function Write-Log { param($Msg) $log.WriteLine("[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Msg") }

Write-Log "Watchdog iniciado (intervalo: ${Interval}s, bridge: $BridgePort)"

while ($true) {
    $bridgeRunning = $false
    $connections = netstat -ano -p TCP 2>$null | Select-String "LISTENING" | Select-String ":$BridgePort"
    if ($connections) {
        $bridgeRunning = $true
        Write-Log "Bridge OK (porta $BridgePort)"
    } else {
        Write-Log "Bridge MORTO na porta $BridgePort - reiniciando..."
        $bridgeScript = "$env:USERPROFILE\Desktop\Codigos\EcoSystemUmGrau\scripts\jarvis_bridge.py"
        if (Test-Path $bridgeScript) {
            $psi = New-Object System.Diagnostics.ProcessStartInfo
            $psi.FileName = "python"
            $psi.Arguments = "-u `"$bridgeScript`""
            $psi.WorkingDirectory = Split-Path $bridgeScript
            $psi.UseShellExecute = $false
            $psi.RedirectStandardOutput = $true
            $psi.RedirectStandardError = $true
            $psi.CreateNoWindow = $true
            $p = [System.Diagnostics.Process]::Start($psi)
            Write-Log "Bridge reiniciado (PID: $($p.Id))"
        } else {
            Write-Log "Bridge script nao encontrado em $bridgeScript"
        }
    }

    $serveConnections = netstat -ano -p TCP 2>$null | Select-String "LISTENING" | Select-String ":8766"
    if ($serveConnections) {
        try {
            $health = Invoke-WebRequest -Uri "http://localhost:8766/api/health" -UseBasicParsing -TimeoutSec 5
            $servePid = ($serveConnections[0] -split '\s+')[-1]
            $proc = Get-Process -Id $servePid -ErrorAction SilentlyContinue
            if ($proc) {
                $memMB = [math]::Round($proc.WorkingSet64 / 1MB, 1)
                $cpuSec = [math]::Round($proc.TotalProcessorTime.TotalSeconds, 0)
                Write-Log "Serve OK (PID $servePid, ${memMB}MB, ${cpuSec}s CPU, health $($health.StatusCode))"
                if ($memMB -gt 500) { Write-Log "ALERTA: Serve com ${memMB}MB - alto consumo" }
            } else {
                Write-Log "Serve OK (PID nao encontrado, health $($health.StatusCode))"
            }
        } catch {
            Write-Log "Serve na porta 8766 mas health check falhou: $_"
        }
    } else {
        Write-Log "Serve MORTO na porta 8766"
    }

    $orphans = Get-Process -Name "opencode" -ErrorAction SilentlyContinue | Where-Object {
        $cmd = (Get-WmiObject Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue).CommandLine
        $cmd -match "opencode\.exe run" -or ($cmd -match "opencode\.exe" -and $cmd -notmatch " serve")
    }
    if ($orphans) {
        $totalMB = 0
        foreach ($p in $orphans) { $totalMB += [math]::Round($p.WorkingSet64 / 1MB, 0) }
        $orphans | Stop-Process -Force
        Write-Log "Limpou $($orphans.Count) processos orfaos do OpenCode (${totalMB}MB liberados)"
    }
    Start-Sleep -Seconds $Interval
}

$log.Close()
