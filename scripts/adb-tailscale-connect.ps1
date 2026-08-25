<#
.SYNOPSIS
    Conecta adb via Tailscale descobrindo a porta wireless debugging via mDNS.
.DESCRIPTION
    Roda adb mdns, extrai a porta do device configurado, conecta IP:PORTA.
    Configuração via variáveis de ambiente ou arquivo local scripts/.adb_tailscale.json (não versionado).
    Variáveis:
      TAILSCALE_IP   - IP do celular na rede Tailscale (padrão 100.64.71.9)
      ADB_MDNS_SERIAL - serial do device no mDNS (padrão adb-6d92eed7)
.PARAMETER TailscaleIP
    Override do IP (opcional).
.EXAMPLE
    .\adb-tailscale-connect.ps1
    $wifi = .\adb-tailscale-connect.ps1
#>
param(
    [string]$TailscaleIP = ""
)

function Write-Log($msg) { Write-Host "[adb-wifi] $msg" -ForegroundColor Cyan }

# Carrega configuração local não versionada
$configPath = Join-Path $PSScriptRoot ".adb_tailscale.json"
$cfg = @{}
if (Test-Path $configPath) {
    $cfg = Get-Content $configPath -Raw | ConvertFrom-Json
}

$ip = $TailscaleIP
if (-not $ip) { $ip = $env:TAILSCALE_IP }
if (-not $ip) { $ip = $cfg.tailscale_ip }
if (-not $ip) { $ip = "100.64.71.9" }

$serial = $env:ADB_MDNS_SERIAL
if (-not $serial) { $serial = $cfg.mdns_serial }
if (-not $serial) { $serial = "adb-6d92eed7" }

function Write-Log($msg) { Write-Host "[adb-wifi] $msg" -ForegroundColor Cyan }

# Roda mdns e extrai a porta do device configurado
$mdns = adb mdns services 2>&1 | Out-String
$pattern = "$serial[^\s]*\s+_adb-tls-connect._tcp\s+\S+:(\d+)"
$match = [regex]::Match($mdns, $pattern)
if (-not $match.Success) {
    Write-Log "ERRO: porta mDNS nao encontrada para $serial"
    Write-Log "mdns output: $mdns"
    return $null
}
$porta = $match.Groups[1].Value

$target = "${ip}:${porta}"
Write-Log "Porta mDNS: $porta | Conectando em $target ..."

$result = adb connect $target 2>&1 | Out-String
if ($result -match 'connected to|already connected') {
    Write-Log "OK! Device conectado: $target"
    Write-Host $target
    return $target
} else {
    Write-Log "ERRO: $result"
    return $null
}
