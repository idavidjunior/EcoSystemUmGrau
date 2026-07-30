param(
    [int]$Interval = 20,
    [string]$BridgePort = "8765",
    [string]$ServePort = "8766",
    [string]$LogPath = "$env:USERPROFILE\Desktop\Codigos\EcoSystemUmGrau\scripts\watchdog_log.txt"
)

$ErrorActionPreference = "SilentlyContinue"
$log = [System.IO.StreamWriter]::new($LogPath, $true)
$log.AutoFlush = $true

function Write-Log { param($Msg) $log.WriteLine("[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Msg") }

Write-Log "Watchdog iniciado (intervalo: ${Interval}s, bridge: $BridgePort, serve: $ServePort)"

while ($true) {

    # Bridge
    $bridgeConn = netstat -ano -p TCP 2>$null | Select-String "LISTENING" | Select-String ":$BridgePort"
    if ($bridgeConn) {
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

    # Serve (opencode serve)
    $serveConn = netstat -ano -p TCP 2>$null | Select-String "LISTENING" | Select-String ":$ServePort"
    if ($serveConn) {
        try {
            $health = Invoke-WebRequest -Uri "http://127.0.0.1:$ServePort/global/health" -UseBasicParsing -TimeoutSec 5
            $servePid = ($serveConn[0] -split '\s+')[-1]
            $proc = Get-Process -Id $servePid -ErrorAction SilentlyContinue
            if ($proc) {
                $memMB = [math]::Round($proc.WorkingSet64 / 1MB, 1)
                Write-Log "Serve OK (PID $servePid, ${memMB}MB, health $($health.StatusCode))"
                if ($memMB -gt 500) { Write-Log "ALERTA: Serve com ${memMB}MB - alto consumo" }
            } else {
                Write-Log "Serve PID $servePid nao encontrado, reiniciando..."
                $serveConn[0] | ForEach-Object { taskkill /F /PID $servePid 2>$null }
                $serveConn = $null
            }
        } catch {
            Write-Log "Serve health falhou, reiniciando... $_"
            $servePid = ($serveConn[0] -split '\s+')[-1]
            taskkill /F /PID $servePid 2>$null
            $serveConn = $null
        }
    }
    if (-not $serveConn) {
        Write-Log "Serve MORTO na porta $ServePort - iniciando..."
        $opencodeBin = "$env:APPDATA\npm\node_modules\opencode-ai\bin\opencode.exe"
        if (Test-Path $opencodeBin) {
            $psi = New-Object System.Diagnostics.ProcessStartInfo
            $psi.FileName = $opencodeBin
            $psi.Arguments = "serve --port $ServePort --hostname 127.0.0.1"
            $psi.WorkingDirectory = "$env:USERPROFILE\Desktop\Codigos"
            $psi.UseShellExecute = $false
            $psi.RedirectStandardOutput = $true
            $psi.RedirectStandardError = $true
            $psi.CreateNoWindow = $true
            $envVars = @{}
            Get-ChildItem Env: | ForEach-Object { $envVars[$_.Name] = $_.Value }
            $psi.EnvironmentVariables.Clear()
            foreach ($kv in $envVars.GetEnumerator()) { $psi.EnvironmentVariables[$kv.Key] = $kv.Value }
            $p = [System.Diagnostics.Process]::Start($psi)
            Write-Log "Serve iniciado (PID: $($p.Id))"
        } else {
            Write-Log "opencode.exe nao encontrado em $opencodeBin"
        }
    }

    # Orphans: mata processos opencode run que sobraram (exclui serve)
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
