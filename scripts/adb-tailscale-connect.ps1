<#
.SYNOPSIS
    Conecta adb via Tailscale (IP fixo 100.64.71.9) descobrindo a porta wireless debugging via mDNS.
.DESCRIPTION
    Roda adb mdns, extrai a porta do redmi-note-11, conecta 100.64.71.9:PORTA.
    Retorna o device id (100.64.71.9:PORTA) para uso em scripts.
.PARAMETER TailscaleIP
    IP do celular na rede Tailscale. Padrao: 100.64.71.9.
.EXAMPLE
    .\adb-tailscale-connect.ps1
    $wifi = .\adb-tailscale-connect.ps1
#>
param(
    [string]$TailscaleIP = "100.64.71.9"
)

function Write-Log($msg) { Write-Host "[adb-wifi] $msg" -ForegroundColor Cyan }

# Roda mdns e extrai a porta do redmi-note-11 (porta vale para qualquer IP do device)
$mdns = adb mdns services 2>&1 | Out-String
$match = [regex]::Match($mdns, 'adb-6d92eed7[^\s]*\s+_adb-tls-connect._tcp\s+\S+:(\d+)')
if (-not $match.Success) {
    Write-Log "ERRO: porta mDNS nao encontrada para adb-6d92eed7"
    Write-Log "mdns output: $mdns"
    return $null
}
$porta = $match.Groups[1].Value

$target = "${TailscaleIP}:${porta}"
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
