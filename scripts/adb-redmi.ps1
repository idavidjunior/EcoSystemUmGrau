# adb-redmi.ps1 - Conecta ADB ao Redmi Note 11 via Tailscale automaticamente
# Detecta o IP atual (IPv4 e IPv6) via tailscale status e executa adb connect.
# Tenta IPv6 primeiro (rota direta do celular) e cai para IPv4 se falhar.
# Uso: .\adb-redmi.ps1 [-debug]
#
# ATENCAO PowerShell: em string interpolada use ${target}:5555 (sem chaves,
# "$target:5555" e interpretado como variavel de escopo "target:5555" -> vazio).

param(
    [switch]$debug,
    [string]$adb = "$env:LOCALAPPDATA\Android\platform-tools\platform-tools\adb.exe",
    [string]$hostPattern = "redmi|Redmi"
)

$ErrorActionPreference = "Stop"
$candidates = @()   # lista de IPs candidatos (IPv6 primeiro, depois IPv4)
$ts = $null

# 1) Coleta candidatos via tailscale status --json (IPv6 + IPv4)
try {
    $j = tailscale status --json 2>&1 | ConvertFrom-Json
    $peer = $j.Peer | Where-Object { $_.HostName -match $hostPattern } | Select-Object -First 1
    if ($peer -and $peer.TailscaleIPs) {
        # IPv6 primeiro
        foreach ($ip in $peer.TailscaleIPs) {
            if ($ip -match ":") { $candidates += $ip.Trim('[', ']') }
        }
        # IPv4 depois
        foreach ($ip in $peer.TailscaleIPs) {
            if ($ip -match "^\d+\.\d+\.\d+\.\d+$") { $candidates += $ip }
        }
        if ($debug) { Write-Host "[dbg] candidatos(json): $($candidates -join ', ')" -ForegroundColor DarkYellow }
    }
} catch {
    if ($debug) { Write-Host "[dbg] tailscale json falhou: $_" -ForegroundColor DarkYellow }
}

# 2) Fallback: texto do tailscale status (o JSON pode nao trazer peers nesta versao)
if ($candidates.Count -eq 0) {
    try {
        $ts = (tailscale status 2>&1) -join "`n"
        $line = $ts -split "`n" | Where-Object { $_ -match $hostPattern } | Select-Object -First 1
        if ($line) {
            if ($debug) { Write-Host "[dbg] linha celular: $line" -ForegroundColor DarkYellow }
            # IPv6 do CurAddr (entre colchetes apos "direct"), ex: [2804:...:e76]:46423
            if ($line -match "\[([0-9a-fA-F:]+)\]:\d+") {
                $v6 = $Matches[1]
                if ($v6 -notin $candidates) { $candidates += $v6 }
            }
            # IPv4 do tailscale (primeira coluna)
            $ip4 = ($line -split "\s+")[0].Trim('[', ']')
            if ($ip4 -match "^\d+\.\d+\.\d+\.\d+$" -and $ip4 -notin $candidates) { $candidates += $ip4 }
            if ($debug) { Write-Host "[dbg] candidatos(texto): $($candidates -join ', ')" -ForegroundColor DarkYellow }
        }
    } catch {
        if ($debug) { Write-Host "[dbg] tailscale texto falhou: $_" -ForegroundColor DarkYellow }
    }
}

if ($candidates.Count -eq 0) {
    Write-Host "[ERRO] Nao encontrei o celular no tailscale. Verifique se o app Tailscale esta ativo no celular." -ForegroundColor Red
    Write-Host "Rode: tailscale status" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $adb)) {
    Write-Host "[ERRO] ADB nao encontrado em: $adb" -ForegroundColor Red
    exit 1
}

# 3) Tenta cada candidato ate conseguir conectar
$connected = $false
foreach ($ip in $candidates) {
    if ($ip -match ":") { $conn = "[${ip}]:5555" } else { $conn = "${ip}:5555" }
    Write-Host "[INFO] Tentando: adb connect $conn" -ForegroundColor Cyan
    $out = & $adb connect $conn 2>&1
    $out | ForEach-Object { Write-Host "  $_" }
    if ($out -match "connected to") {
        $connected = $true
        Write-Host "[OK] Conectado via $conn" -ForegroundColor Green
        break
    }
}

Write-Host ""
if (-not $connected) {
    Write-Host "[ERRO] Nenhum IP respondeu. O adbd do celular pode estar fora (apos reboot, adb tcpip nao persiste)." -ForegroundColor Red
    Write-Host "Solucao: conecte o USB e rode: adb tcpip 5555  (ou use Wireless Debugging pareando em adb pair)." -ForegroundColor Yellow
    exit 1
}

Write-Host "=== Devices ===" -ForegroundColor Cyan
& $adb devices

Write-Host ""
Write-Host "Dica: rode '.\adb-redmi.ps1 -debug' para ver o diagnostico." -ForegroundColor DarkGray
