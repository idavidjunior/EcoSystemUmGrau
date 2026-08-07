param(
    [int]$Interval = 20,
    [string]$BridgePort = "8765",
    [string]$ServePort = "8767",
    [string]$LogPath = "$PSScriptRoot\watchdog_log.txt"
)

$ErrorActionPreference = "SilentlyContinue"

# Instância única via arquivo de lock com PID (mais robusto que Mutex nomeado:
# um Mutex abandoned no Windows não é re-adquirido e trava o restart).
$LockPath = "$PSScriptRoot\watchdog.lock"
$meuPid = $PID
$jaExiste = $false
if (Test-Path $LockPath) {
    try {
        $outroPid = [int](Get-Content $LockPath -Raw).Trim()
        $procOutro = Get-Process -Id $outroPid -ErrorAction SilentlyContinue
        if ($procOutro -and $procOutro.ProcessName -match "powershell") {
            $jaExiste = $true
        }
    } catch { }
}
if ($jaExiste) {
    exit 0
}
try { Set-Content -Path $LockPath -Value $meuPid -Encoding ascii } catch { }

# Log com limite de tamanho (~2MB): ao estourar, descarta a metade mais antiga.
if (Test-Path $LogPath) {
    $info = Get-Item $LogPath
    if ($info.Length -gt 2MB) {
        $linhas = Get-Content $LogPath
        $linhas | Select-Object -Skip ([int]($linhas.Count / 2)) | Set-Content $LogPath
    }
}
$log = [System.IO.StreamWriter]::new($LogPath, $true)
$log.AutoFlush = $true

function Write-Log { param($Msg) $log.WriteLine("[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Msg") }

$env:Path = "C:\Program Files\Eclipse Adoptium\jdk-17.0.20.8-hotspot\bin;" + $env:Path
$PYTHON = "C:\Users\David Jr\AppData\Local\Programs\Python\Python312\python.exe"
$WORKDIR = "C:\Users\David Jr\Documents\Default Project"
$SCRIPTS = Join-Path $WORKDIR "EcoSystemUmGrau\scripts"
$OPENCODE_BIN = Join-Path $env:APPDATA "npm\node_modules\opencode-ai\bin\opencode.exe"

# Credenciais do serve (Basic Auth) — mesma origem que a bridge (scripts/.env)
$SERVER_USER = "opencode"
$SERVER_PASS = $env:OPENCODE_SERVER_PASSWORD
if (-not $SERVER_PASS) {
    $envFile = Join-Path $SCRIPTS ".env"
    if (Test-Path $envFile) {
        $linha = Get-Content $envFile | Where-Object { $_ -match '^OPENCODE_SERVER_PASSWORD=' } | Select-Object -First 1
        if ($linha) { $SERVER_PASS = ($linha -replace '^OPENCODE_SERVER_PASSWORD=', '').Trim().Trim('"') }
    }
}
$AUTH_B64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("${SERVER_USER}:${SERVER_PASS}"))
$AUTH_HEADERS = @{ Authorization = "Basic $AUTH_B64" }

function Test-BridgeUp { param($Port) (netstat -ano -p TCP 2>$null | Select-String "LISTENING" | Select-String ":$Port") -ne $null }
function Test-ServeUp {
    param($Port)
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/global/health" -Headers $AUTH_HEADERS -UseBasicParsing -TimeoutSec 5
        return ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300)
    } catch {
        return $false
    }
}
# Health-check do bridge: porta LISTENING + processo dono vivo + escreve no log.
# Se a porta estiver LISTENING com socket órfão (processo morto), reinicia.
function Test-BridgeAlive {
    param($Port)
    $linha = netstat -ano -p TCP 2>$null | Select-String "LISTENING" | Select-String ":$Port" | Select-Object -First 1
    if (-not $linha) { return $false }
    $pidStr = ($linha.ToString() -split '\s+')[-1]
    if ($pidStr -notmatch '^\d+$') { return $false }
    $proc = Get-Process -Id ([int]$pidStr) -ErrorAction SilentlyContinue
    return ($proc -ne $null)
}
function Get-BridgePid {
    param($Port)
    $linha = netstat -ano -p TCP 2>$null | Select-String "LISTENING" | Select-String ":$Port" | Select-Object -First 1
    if (-not $linha) { return $null }
    $pidStr = ($linha.ToString() -split '\s+')[-1]
    if ($pidStr -notmatch '^\d+$') { return $null }
    return [int]$pidStr
}

Write-Log "Watchdog iniciado (intervalo: ${Interval}s, bridge: $BridgePort, serve: $ServePort)"

while ($true) {

    # ============ BRIDGE ============
    if (Test-BridgeAlive $BridgePort) {
        Write-Log "Bridge OK (PID $(Get-BridgePid $BridgePort))"
    } else {
        if (Test-BridgeUp $BridgePort) {
            # Porta LISTENING mas processo dono morto: socket órfão.
            $orphanPid = Get-BridgePid $BridgePort
            Write-Log "Bridge com socket orfao (PID $orphanPid) - limpando handle..."
            taskkill /F /PID $orphanPid 2>$null | Out-Null
            Start-Sleep -Seconds 3
        }
        Write-Log "Bridge MORTO na porta $BridgePort - reiniciando..."
        if (Test-Path $PYTHON) {
            $psi = New-Object System.Diagnostics.ProcessStartInfo
            $psi.FileName = $PYTHON
            $psi.Arguments = "-u `"$SCRIPTS\jarvis_bridge.py`""
            $psi.WorkingDirectory = $SCRIPTS
            $psi.UseShellExecute = $false
            $psi.CreateNoWindow = $true
            $p = [System.Diagnostics.Process]::Start($psi)
            Write-Log "Bridge reiniciado (PID: $($p.Id))"
        } else {
            Write-Log "Python nao encontrado em $PYTHON"
        }
    }

    # ============ SERVE (opencode) ============
    $serveUp = Test-BridgeUp $ServePort
    if ($serveUp) {
        $servePid = ((netstat -ano -p TCP 2>$null | Select-String "LISTENING" | Select-String ":$ServePort")[0] -split '\s+')[-1]
        $proc = Get-Process -Id $servePid -ErrorAction SilentlyContinue
        if ($proc -and (Test-ServeUp $ServePort)) {
            $memMB = [math]::Round($proc.WorkingSet64 / 1MB, 1)
            Write-Log "Serve OK (PID $servePid, ${memMB}MB)"
            if ($memMB -gt 800) { Write-Log "ALERTA: Serve com ${memMB}MB - alto consumo" }
        } else {
            Write-Log "Serve na porta $ServePort nao responde ou PID morto - reiniciando..."
            if ($servePid -match '^\d+$') {
                taskkill /F /PID $servePid 2>$null | Out-Null
                Start-Sleep -Seconds 2
            }
        }
    } else {
        Write-Log "Serve MORTO na porta $ServePort - iniciando..."
    }
    if (-not (Test-BridgeUp $ServePort)) {
        if (Test-Path $OPENCODE_BIN) {
            $psi = New-Object System.Diagnostics.ProcessStartInfo
            $psi.FileName = $OPENCODE_BIN
            $psi.Arguments = "serve --port $ServePort"
            $psi.WorkingDirectory = $WORKDIR
            $psi.UseShellExecute = $false
            $psi.CreateNoWindow = $true
            $envVars = @{}
            Get-ChildItem Env: | ForEach-Object { $envVars[$_.Name] = $_.Value }
            $envVars["OPENCODE_SERVER_USERNAME"] = $SERVER_USER
            $envVars["OPENCODE_SERVER_PASSWORD"] = $SERVER_PASS
            $psi.EnvironmentVariables.Clear()
            foreach ($kv in $envVars.GetEnumerator()) { $psi.EnvironmentVariables[$kv.Key] = $kv.Value }
            $p = [System.Diagnostics.Process]::Start($psi)
            Write-Log "Serve iniciado (PID: $($p.Id))"
        } else {
            Write-Log "opencode.exe nao encontrado em $OPENCODE_BIN"
        }
    }

    # ============ ORPHANS ============
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
try { Remove-Item -Path $LockPath -Force -ErrorAction SilentlyContinue } catch {}
