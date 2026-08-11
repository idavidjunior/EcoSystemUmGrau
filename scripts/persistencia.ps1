# ============================================================================
# persistencia.ps1 - PONTO UNICO DE PERSISTENCIA (gate)
#
# Responsavel por TODOS os commits/push do ecossistema (EcoSystemUmGrau,
# ler-runtime e projetos Android). Nenhum outro script, servico ou agente
# deve executar git add/commit/push automaticamente. Quando o gate estiver
# em modo MANUAL, nada e commitado automaticamente; as pendencias ficam
# retidas no working tree ate um commit manual.
#
# Uso:
#   persistencia.ps1 status                     -> estado atual (modo + pendencias)
#   persistencia.ps1 auto                       -> modo automatico (padrao)
#   persistencia.ps1 manual                     -> pausa commits automaticos
#   persistencia.ps1 commit -Repo eco -Mensagem "..." [-Push]
#                                               -> commit manual (funciona em qualquer modo)
#   persistencia.ps1 sync [-Push]               -> commit manual de todos os repos
#   persistencia.ps1 run-sync -Repo <key> -Label <x> [-Push]   (uso interno dos servicos)
#
# -Repo: "eco" | "ler" | "proj:<path>" | path absoluto
# ============================================================================
param(
    [string]$Comando = "status",
    [string]$Repo = "eco",
    [string]$Mensagem = "",
    [string]$Label = "gate",
    [switch]$Push
)

$ErrorActionPreference = "Continue"
$ecoDir = Split-Path $PSScriptRoot -Parent
$lerDir = "$ecoDir\ler-runtime"
$configFile = "$ecoDir\config\persistencia.json"
$logFile = "$env:USERPROFILE\.persistencia.log"
$projectsDir = "$env:USERPROFILE\Documents\Default Project"
$tempDir = $env:TEMP

function Write-Log {
    param([string]$Msg)
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Msg"
    try { Add-Content -Path $logFile -Value $line -Encoding UTF8 -ErrorAction Stop } catch {}
}

function Get-Config {
    if (Test-Path $configFile) {
        try { return (Get-Content $configFile -Raw -Encoding UTF8 | ConvertFrom-Json) } catch {}
    }
    return [pscustomobject]@{ modo = 'auto'; excluir = @() }
}

function Set-Config {
    param($Cfg)
    $Cfg | ConvertTo-Json -Depth 6 | Set-Content -Path $configFile -Encoding UTF8 -Force
}

function Get-RepoPath {
    param([string]$Key)
    switch -Regex ($Key) {
        '^(eco|root)$'       { return $ecoDir }
        '^(ler|ler-runtime)$' { return $lerDir }
        '^proj:(.+)$'        { return $Matches[1].Trim() }
        default {
            if (Test-Path $Key) { return $Key }
            return $ecoDir
        }
    }
}

function Get-LockPath {
    param([string]$RepoPath)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($RepoPath.ToLower())
    $hash = ([System.Security.Cryptography.MD5]::Create()).ComputeHash($bytes)
    $hex = [System.BitConverter]::ToString($hash).Replace('-', '').Substring(0, 12)
    return "$tempDir\persistencia-$hex.lock"
}

function Test-Lock {
    param([string]$Path)
    if (Test-Path $Path) {
        $age = (Get-Date) - (Get-Item $Path).LastWriteTime
        if ($age.TotalSeconds -lt 120) { return $true }
        Remove-Item $Path -Force -ErrorAction SilentlyContinue
    }
    return $false
}

function Get-Pendentes {
    param([string]$Path)
    if (-not (Test-Path "$Path\.git")) { return '' }
    Push-Location $Path
    $s = git status --porcelain 2>&1 | Out-String
    Pop-Location
    return $s.Trim()
}

function Invoke-RepoCommit {
    param([string]$RepoKey, [string]$MsgLabel, [switch]$DoPush, [string]$UserMsg)
    $path = Get-RepoPath $RepoKey
    if (-not (Test-Path "$path\.git")) { Write-Log "SKIP $RepoKey (sem .git)"; return 'SKIP' }
    $lock = Get-LockPath $path
    if (Test-Lock $lock) { Write-Log "LOCK ocupado, pulando $RepoKey"; return 'LOCKED' }
    New-Item -Path $lock -ItemType File -Force -ErrorAction SilentlyContinue | Out-Null
    try {
        $cfg = Get-Config
        Push-Location $path
        if ($DoPush) {
            $pullOut = git pull --ff-only 2>&1 | Out-String
            if ($pullOut -match 'CONFLICT|conflict|Automatic merge failed') {
                Write-Log "PULL ${RepoKey}: CONFLITO"
                Pop-Location; Remove-Item $lock -Force -ErrorAction SilentlyContinue
                return 'CONFLICT'
            }
            if ($pullOut -match 'Fast-forward|Updating') { Write-Log "PULL ${RepoKey}: OK" }
        }
        $status = git status --porcelain 2>&1 | Out-String
        if (-not $status.Trim()) {
            Pop-Location; Remove-Item $lock -Force -ErrorAction SilentlyContinue
            return 'CLEAN'
        }
        git add -A 2>&1 | Out-Null
        foreach ($ex in @($cfg.excluir)) {
            if ($ex) { git reset -q -- "$ex" 2>&1 | Out-Null }
        }
        $msg = ''
        if ($UserMsg) { $msg = $UserMsg }
        else { $msg = "[gate] $MsgLabel - $(Get-Date -Format 'yyyy-MM-dd HH:mm')" }
        git commit -m $msg 2>&1 | Out-Null
        $commitHash = git rev-parse --short HEAD 2>$null
        Write-Log "COMMIT ${RepoKey}: $commitHash - $msg"
        if ($DoPush) {
            $pushOut = git push 2>&1 | Out-String
            Write-Log "PUSH ${RepoKey}: $($pushOut.Trim())"
        }
        Pop-Location
        Remove-Item $lock -Force -ErrorAction SilentlyContinue
        return "COMMIT:$commitHash"
    } catch {
        Write-Log "ERRO ${RepoKey}: $_"
        Pop-Location
        Remove-Item $lock -Force -ErrorAction SilentlyContinue
        return 'ERROR'
    }
}

# ----------------------------------------------------------------------------
# Dispatch
# ----------------------------------------------------------------------------
$cfg = Get-Config

if ($Comando -eq 'auto') {
    $cfg.modo = 'auto'
    Set-Config $cfg
    Write-Host '[PERSISTENCIA] Modo AUTO ativado. Commits automaticos liberados.' -ForegroundColor Green
    Write-Log 'MODO AUTO'
    exit 0
}

if ($Comando -eq 'manual') {
    $cfg.modo = 'manual'
    Set-Config $cfg
    Write-Host '[PERSISTENCIA] Modo MANUAL ativado. Commits automaticos pausados. Use "persistencia.ps1 commit" para commit manual.' -ForegroundColor Yellow
    Write-Log 'MODO MANUAL'
    exit 0
}

if ($Comando -eq 'run-sync') {
    if ($cfg.modo -eq 'manual') {
        $pend = Get-Pendentes (Get-RepoPath $Repo)
        if ($pend) {
            Write-Log "MANUAL: pendencia retida em $Repo aguardando commit manual"
            Write-Host '[PERSISTENCIA] modo MANUAL - nada commitado (pendencia retida)' -ForegroundColor Yellow
        } else {
            Write-Host '[PERSISTENCIA] modo MANUAL - sem pendencias' -ForegroundColor Gray
        }
        exit 0
    }
    $r = Invoke-RepoCommit -RepoKey $Repo -MsgLabel $Label -DoPush:$Push
    $color = if ($r -like 'COMMIT*') { 'Green' } else { 'Gray' }
    Write-Host "[PERSISTENCIA] $Repo -> $r" -ForegroundColor $color
    exit 0
}

if ($Comando -eq 'commit') {
    $r = Invoke-RepoCommit -RepoKey $Repo -MsgLabel $Label -DoPush:$Push -UserMsg $Mensagem
    Write-Host "[PERSISTENCIA] commit manual $Repo -> $r" -ForegroundColor Green
    exit 0
}

if ($Comando -eq 'sync') {
    $repos = @('eco', 'ler')
    if (Test-Path $projectsDir) {
        Get-ChildItem $projectsDir -Directory | Where-Object {
            (git -C $_.FullName remote -v 2>&1) -match 'fetch' -and
            (Test-Path "$($_.FullName)\.git") -and $_.FullName -ne $ecoDir
        } | ForEach-Object { $repos += $_.FullName }
    }
    foreach ($r in $repos) {
        $res = Invoke-RepoCommit -RepoKey $r -MsgLabel $Label -DoPush:$Push -UserMsg $Mensagem
        Write-Host "[PERSISTENCIA] $r -> $res"
    }
    exit 0
}

# status (padrao)
Write-Host '=== PONTO UNICO DE PERSISTENCIA ===' -ForegroundColor Cyan
Write-Host "Modo: $(if ($cfg.modo -eq 'manual') { 'MANUAL (commits pausados)' } else { 'AUTO' })"
Write-Host "Config: $configFile"
Write-Host ''
foreach ($k in @('eco', 'ler')) {
    $p = Get-RepoPath $k
    if (-not (Test-Path "$p\.git")) { continue }
    $head = git -C $p rev-parse --short HEAD 2>$null
    $pend = Get-Pendentes $p
    Write-Host "$k ($head):" -ForegroundColor Gray
    if ($pend) {
        $pend -split "`n" | Select-Object -First 12 | ForEach-Object { Write-Host "   $_" -ForegroundColor Yellow }
    } else {
        Write-Host '   (sem pendencias)' -ForegroundColor DarkGray
    }
}
if (Test-Path $projectsDir) {
    $projs = Get-ChildItem $projectsDir -Directory | Where-Object {
        (git -C $_.FullName remote -v 2>&1) -match 'fetch' -and
        (Test-Path "$($_.FullName)\.git") -and $_.FullName -ne $ecoDir
    }
    if ($projs) {
        Write-Host 'Projetos Android:' -ForegroundColor Gray
        foreach ($pr in $projs) {
            $pp = Get-Pendentes $pr.FullName
            Write-Host "   $($pr.Name): $(if ($pp) { 'PENDENTE' } else { 'limpo' })" -ForegroundColor DarkGray
        }
    }
}
Write-Host ''
if (Test-Path $logFile) {
    Write-Host 'Ultimas entradas do log:' -ForegroundColor Gray
    Get-Content $logFile -Tail 5
}
exit 0
