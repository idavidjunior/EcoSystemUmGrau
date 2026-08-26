<#
.SYNOPSIS
    Script autônomo de diagnóstico, correção e conexão ADB.
.DESCRIPTION
    Fluxo completo (em ordem):
    1. Matar processos ADB e Tailscale travados
    2. Reiniciar Tailscale (serviço ou daemon manual)
    3. Reiniciar ADB server
    4. Detectar e conectar via USB
    5. Detectar e conectar via Tailscale (IP direto)
    6. Detectar e conectar via mDNS (Wireless Debugging)
    7. Detectar e conectar via WiFi local (IPs da rede)
    8. Fallback: tentar adb-redmi.ps1
    9. Reportar status final
.PARAMETER Fix
    Tenta corrigir serviços (Tailscale, ADB) antes de conectar.
.PARAMETER Verbose
    Saída detalhada.
.PARAMETER Json
    Retorna resultado em JSON.
.EXAMPLE
    .\adb_ensure_connect.ps1
    .\adb_ensure_connect.ps1 -Fix
    .\adb_ensure_connect.ps1 -Json
#>
param(
    [switch]$Fix,
    [switch]$Verbose,
    [switch]$Json
)

$ErrorActionPreference = "Continue"
$results = @()
$connected = $false
$connectedMethod = ""
$connectedSerial = ""

function Write-Msg($msg, $color = "White") {
    if (-not $Json) { Write-Host $msg -ForegroundColor $color }
}
function Write-Step($step, $msg) {
    $results += @{ step = $step; message = $msg }
    Write-Msg "[$step] $msg" Cyan
}
function Write-Ok($msg) {
    $results += @{ step = "OK"; message = $msg }
    Write-Msg "[OK] $msg" Green
}
function Write-Fail($msg) {
    $results += @{ step = "FAIL"; message = $msg }
    Write-Msg "[FAIL] $msg" Red
}

# ADB path
$adbCandidates = @(
    "$env:LOCALAPPDATA\Android\platform-tools\platform-tools\adb.exe",
    "$env:LOCALAPPDATA\Android\platform-tools\adb.exe",
    "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe",
    "$env:PROGRAMFILES\Android\platform-tools\adb.exe"
)
$adb = $null
foreach ($c in $adbCandidates) {
    if (Test-Path $c) { $adb = $c; break }
}
if (-not $adb) {
    $where = (Get-Command adb -ErrorAction SilentlyContinue).Source
    if ($where) { $adb = $where }
}
if (-not $adb) {
    Write-Fail "ADB nao encontrado"
    if ($Json) { @{ ok = $false; error = "ADB nao encontrado" } | ConvertTo-Json -Depth 5 } else { exit 1 }
    return
}

Write-Msg "ADB: $adb" DarkGray

# ===== STEP 1: Kill stale processes =====
Write-Step "STEP1" "Matando processos travados..."
Get-Process -Name "adb*" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Msg "  Matar adb PID $($_.Id)" DarkGray
    Stop-Process -Id $_.Id -Force 2>$null
}
Start-Sleep 1
Write-Msg "  Processos limpos" DarkGray

# ===== STEP 2: Check for connected devices (quick) =====
Write-Step "STEP2" "Verificando dispositivos ja conectados..."
try {
    $devOut = & $adb devices 2>&1
    $devLines = ($devOut | Out-String) -split "`n"
    $devices = @()
    foreach ($line in $devLines) {
        $line = $line.Trim()
        if ($line -and $line -notmatch "^List|^$" -and $line -match "\s") {
            $parts = $line -split "\s+"
            if ($parts.Count -ge 2 -and $parts[1] -eq "device") {
                $devices += $parts[0]
            }
        }
    }
    if ($devices.Count -gt 0) {
        $connected = $true
        $connectedMethod = "already_connected"
        $connectedSerial = $devices[0]
        Write-Ok "Ja conectado: $($devices -join ', ')"
    }
} catch {
    Write-Msg "  adb devices falhou: $_" DarkGray
}

# ===== STEP 3: USB Check =====
if (-not $connected) {
    Write-Step "STEP3" "Verificando USB..."
    try {
        $usbOut = & $adb devices -l 2>&1 | Out-String
        if ($usbOut -match "usb:") {
            $connected = $true
            $connectedMethod = "usb"
            $m = [regex]::Match($usbOut, "(\S+)\s+device\s+usb:")
            if ($m.Success) { $connectedSerial = $m.Groups[1].Value }
            Write-Ok "USB conectado: $connectedSerial"
        } else {
            Write-Msg "  Nenhum USB detectado" DarkGray
        }
    } catch {
        Write-Msg "  USB check falhou" DarkGray
    }
}

# ===== STEP 4: Fix Tailscale (if -Fix) =====
if ($Fix -and -not $connected) {
    Write-Step "STEP4" "Corrigindo Tailscale..."

    # Try to start the service
    $svc = Get-Service Tailscale -ErrorAction SilentlyContinue
    if ($svc -and $svc.Status -ne "Running") {
        Write-Msg "  Servico Tailscale: $($svc.Status). Tentando iniciar..." DarkGray
        try {
            Start-Service Tailscale -ErrorAction Stop
            Start-Sleep 3
            Write-Msg "  Servico Tailscale iniciado" DarkGray
        } catch {
            Write-Msg "  Falha ao iniciar servico: $_" DarkGray
            # Try manual daemon
            $tsd = "C:\Program Files\Tailscale\tailscaled.exe"
            if (Test-Path $tsd) {
                Write-Msg "  Tentando daemon manual..." DarkGray
                Start-Process $tsd -WindowStyle Hidden
                Start-Sleep 3
                $ts = "C:\Program Files\Tailscale\tailscale.exe"
                if (Test-Path $ts) {
                    Start-Process $ts -ArgumentList "up" -WindowStyle Hidden
                    Start-Sleep 5
                }
            }
        }
    }

    # Verify Tailscale is up
    $tsExe = "C:\Program Files\Tailscale\tailscale.exe"
    if (Test-Path $tsExe) {
        $tsStatus = & $tsExe status 2>&1 | Out-String
        if ($tsStatus -match "Connected") {
            Write-Ok "Tailscale conectado"
        } else {
            Write-Fail "Tailscale ainda offline. Pode precisar login manual."
        }
    }
}

# ===== STEP 5: ADB Server restart =====
if (-not $connected) {
    Write-Step "STEP5" "Reiniciando ADB server..."
    try {
        & $adb kill-server 2>$null
        Start-Sleep 1
        & $adb start-server 2>$null
        Start-Sleep 2
        Write-Msg "  ADB server reiniciado" DarkGray
    } catch {
        Write-Msg "  Falha ao reiniciar ADB: $_" DarkGray
    }

    # Re-check
    try {
        $devOut = & $adb devices 2>&1 | Out-String
        if ($devOut -match "device`$") {
            $connected = $true
            $connectedMethod = "adb_server_restart"
            Write-Ok "Conectado apos reiniciar ADB server"
        }
    } catch {}
}

# ===== STEP 6: Tailscale direct IP =====
if (-not $connected) {
    Write-Step "STEP6" "Tentando Tailscale IP direto..."

    # Try to discover the current Tailscale IP
    $tsExe = "C:\Program Files\Tailscale\tailscale.exe"
    $tailscaleIP = $null

    if (Test-Path $tsExe) {
        try {
            $tsJson = & $tsExe status --json 2>&1 | Out-String
            $tsData = $tsJson | ConvertFrom-Json -ErrorAction SilentlyContinue
            if ($tsData -and $tsData.Peer) {
                foreach ($peer in $tsData.Peer.PSObject.Properties) {
                    $hn = $peer.Value.HostName
                    if ($hn -match "redmi|Redmi|Xiaomi|xiaomi|6d92eed7") {
                        if ($peer.Value.TailscaleIPs) {
                            foreach ($ip in $peer.Value.TailscaleIPs) {
                                if ($ip -match "^\d+\.\d+\.\d+\.\d+$") {
                                    $tailscaleIP = $ip
                                    break
                                }
                            }
                        }
                    }
                }
            }
        } catch {
            Write-Msg "  tailscale status --json falhou" DarkGray
        }
    }

    if (-not $tailscaleIP) {
        # Fallback: hardcoded known IPs
        $tailscaleIP = "100.64.71.9"
    }

    # Try mDNS port first, then 5555
    $port = 5555
    try {
        $mdnsOut = & $adb mdns services 2>&1 | Out-String
        $mPort = [regex]::Match($mdnsOut, "_adb-tls-connect._tcp\S*\s+\S+:(\d+)")
        if ($mPort.Success) {
            $port = [int]$mPort.Groups[1].Value
            Write-Msg "  Porta mDNS: $port" DarkGray
        }
    } catch {}

    foreach ($p in @($port, 5555)) {
        $target = "${tailscaleIP}:${p}"
        Write-Msg "  Tentando $target..." DarkGray
        try {
            $connOut = & $adb connect $target 2>&1 | Out-String
            if ($connOut -match "connected to|already connected") {
                $connected = $true
                $connectedMethod = "tailscale:$target"
                Write-Ok "Conectado via Tailscale: $target"
                break
            }
        } catch {}
    }
}

# ===== STEP 7: WiFi local (all network interfaces) =====
if (-not $connected) {
    Write-Step "STEP7" "Tentando WiFi local..."
    $localIPs = @()
    try {
        $ifaces = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
            Where-Object { $_.IPAddress -notmatch "^127\.|^169\.254\." -and $_.PrefixOrigin -ne "WellKnown" }
        foreach ($iface in $ifaces) {
            $localIPs += $iface.IPAddress
        }
    } catch {
        # Fallback: socket
        try {
            $hn = [System.Net.Dns]::GetHostName()
            foreach ($ai in [System.Net.Dns]::GetHostAddresses($hn)) {
                $ip = $ai.IPAddressToString
                if ($ip -match "^192\.168\.|^10\.|^172\.") { $localIPs += $ip }
            }
        } catch {}
    }

    foreach ($ip in $localIPs) {
        foreach ($p in @(5555)) {
            $target = "${ip}:${p}"
            Write-Msg "  Tentando $target..." DarkGray
            try {
                $connOut = & $adb connect $target 2>&1 | Out-String
                if ($connOut -match "connected to|already connected") {
                    $connected = $true
                    $connectedMethod = "wifi_local:$target"
                    Write-Ok "Conectado via WiFi local: $target"
                    break
                }
            } catch {}
        }
        if ($connected) { break }
    }
}

# ===== STEP 8: mDNS discovery =====
if (-not $connected) {
    Write-Step "STEP8" "Tentando mDNS discovery..."
    try {
        $mdnsOut = & $adb mdns services 2>&1 | Out-String
        $mPort = [regex]::Match($mdnsOut, "_adb-tls-connect._tcp\S*\s+\S+:(\d+)")
        if ($mPort.Success) {
            $port = $mPort.Groups[1].Value
            foreach ($ip in $localIPs) {
                $target = "${ip}:${port}"
                Write-Msg "  Tentando mDNS $target..." DarkGray
                try {
                    $connOut = & $adb connect $target 2>&1 | Out-String
                    if ($connOut -match "connected to|already connected") {
                        $connected = $true
                        $connectedMethod = "mdns:$target"
                        Write-Ok "Conectado via mDNS: $target"
                        break
                    }
                } catch {}
            }
        }
    } catch {}
}

# ===== STEP 9: adb-redmi.ps1 fallback =====
if (-not $connected) {
    Write-Step "STEP9" "Fallback: adb-redmi.ps1..."
    $redmiScript = Join-Path $PSScriptRoot "adb-redmi.ps1"
    if (Test-Path $redmiScript) {
        try {
            $r = & powershell -ExecutionPolicy Bypass -File $redmiScript -debug 2>&1 | Out-String
            if ($r -match "Conectado|connected") {
                $connected = $true
                $connectedMethod = "adb-redmi"
                Write-Ok "Conectado via adb-redmi.ps1"
            } else {
                Write-Fail "adb-redmi.ps1 falhou"
            }
        } catch {
            Write-Fail "adb-redmi.ps1 erro: $_"
        }
    } else {
        Write-Msg "  adb-redmi.ps1 nao encontrado" DarkGray
    }
}

# ===== FINAL: Verify and report =====
Write-Step "FINAL" "Verificando status final..."
Start-Sleep 1
try {
    $finalOut = & $adb devices 2>&1 | Out-String
    $devices = @()
    foreach ($line in ($finalOut -split "`n")) {
        $line = $line.Trim()
        if ($line -and $line -notmatch "^List|^$" -and $line -match "\s") {
            $parts = $line -split "\s+"
            if ($parts.Count -ge 2 -and $parts[1] -eq "device") {
                $devices += @{ id = $parts[0]; state = $parts[1] }
            }
        }
    }
    if ($devices.Count -gt 0 -and -not $connected) {
        $connected = $true
        $connectedMethod = "verified_final"
        $connectedSerial = $devices[0].id
    }
} catch {}

# Output
if ($connected) {
    Write-Ok "CONECTADO! Metodo: $connectedMethod"
    & $adb devices
} else {
    Write-Fail "FALHOU em todos os metodos."
    Write-Msg "Possiveis causas:" Yellow
    Write-Msg "  1. Celular com Tailscale desligado" Yellow
    Write-Msg "  2. Wireless Debugging desligado no celular" Yellow
    Write-Msg "  3. Celular em sleep profundo (pressione power)" Yellow
    Write-Msg "  4. Cabo USB desconectado" Yellow
}

if ($Json) {
    @{
        ok = $connected
        method = $connectedMethod
        serial = $connectedSerial
        adb = $adb
        steps = $results
        devices = $devices
    } | ConvertTo-Json -Depth 5
}
