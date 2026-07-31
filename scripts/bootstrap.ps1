# bootstrap.ps1 — Configura o ecossistema do zero
Write-Host "=== Bootstrap do Ecossistema ===" -ForegroundColor Cyan

$ecoDir = Split-Path $PSScriptRoot -Parent
$lerDir = "$env:USERPROFILE\.ler"
$profilePath = "$env:USERPROFILE\Documents\WindowsPowerShell\profile.ps1"

# 1. Profile
Write-Host "[1/4] Profile ja configurado." -ForegroundColor Green

# 2. Vigilante
$vJob = Get-Job -Name "Vigilante*" -ErrorAction SilentlyContinue
if (-not $vJob) {
    & "$ecoDir\scripts\vigilante.ps1"
    Write-Host "[2/4] Vigilante iniciado." -ForegroundColor Green
} else {
    Write-Host "[2/4] Vigilante ja ativo." -ForegroundColor Green
}

# 3. Verifica LER e seed
if (Test-Path "$lerDir\agent\knowledge_consolidator.py") {
    Write-Host "[3/4] LER KnowledgeConsolidator OK." -ForegroundColor Green
} else {
    Write-Host "[3/4] LER nao encontrado em $lerDir" -ForegroundColor Yellow
}

# 4. Verifica git
Push-Location $ecoDir
$gitRemote = git remote -v 2>$null
if ($gitRemote) {
    Write-Host "[4/4] Git OK." -ForegroundColor Green
} else {
    Write-Host "[4/4] Git sem remote." -ForegroundColor Yellow
}
Pop-Location

Write-Host "=== Bootstrap concluido ===" -ForegroundColor Cyan
Write-Host "Vigilante: & '$ecoDir\scripts\vigilante.ps1 -Status'"
Write-Host "Parar: & '$ecoDir\scripts\vigilante.ps1 -Stop'"
