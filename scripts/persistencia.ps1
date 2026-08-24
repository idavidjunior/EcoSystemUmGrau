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
$projectsDir = "$ecoDir\Projetos"
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
            if (Test-Path -LiteralPath $Key) { return $Key }
            if (Test-Path -LiteralPath "$projectsDir\$Key") { return "$projectsDir\$Key" }
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

function Get-TipoPendencia {
    param([string]$Caminho, [string]$RepoPath)
    if ($Caminho -match '(^|[\\/])(conhecimento[\\/]memoria|ler-runtime[\\/]knowledge|runtime|build[\\/]CerebroVivo)([\\/]|$)') { return 'vivo' }
    if ($Caminho -match 'tfidf|knowledge_graph\.json$|CONHECIMENTO\.md$|cluster_mapper') { return 'vivo' }
    if ($Caminho -match '[\\/]$|^\s*$') { return 'vivo' }
    if ($Caminho.EndsWith('/') -or $Caminho.EndsWith('\')) {
        $cheia = Join-Path $RepoPath $Caminho.TrimEnd('\/')
        if (Test-Path $cheia) {
            $temCodigo = Get-ChildItem $cheia -Recurse -File -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -match '\.(py|js|kt|java|json|xml|ps1)$' } | Select-Object -First 1
            if ($temCodigo) { return 'codigo' }
        }
        return 'vivo'
    }
    if ($Caminho -match '\.(py|ps1|js|html|css|kt|java|kts|gradle|json|xml)$') { return 'codigo' }
    return 'vivo'
}

function Test-PreFlightCodigo {
    param([string]$RepoPath, [string[]]$Arquivos)
    $falhas = New-Object System.Collections.Generic.List[string]
    foreach ($a in $Arquivos) {
        $full = Join-Path $RepoPath $a
        if (-not (Test-Path -LiteralPath $full)) { continue }
        if ($a -match '\.py$') {
            python -m py_compile $full *> $null
            if ($LASTEXITCODE -ne 0) { $falhas.Add($a) }
        } elseif ($a -match '\.js$' -and (Get-Command node -ErrorAction SilentlyContinue)) {
            node --check $full *> $null
            if ($LASTEXITCODE -ne 0) { $falhas.Add($a) }
        }
    }
    return $falhas
}

function Test-ArquivoTrackeado {
    param([string]$RepoPath, [string]$CaminhoRelativo)
    if ([string]::IsNullOrWhiteSpace($CaminhoRelativo)) { return $false }
    $r = git -C $RepoPath ls-files -- $CaminhoRelativo 2>$null
    return [bool]($r | Where-Object { $_.Trim() })
}

function Add-GitignoreLixo {
    param([string]$RepoPath)
    $gi = Join-Path $RepoPath '.gitignore'
    $alvo = @('__pycache__/', '*.pyc')
    $atuais = @()
    if (Test-Path $gi) { $atuais = @(Get-Content $gi -ErrorAction SilentlyContinue | ForEach-Object { $_.Trim() }) }
    $faltam = @($alvo | Where-Object { $atuais -notcontains $_ })
    if ($faltam.Count -gt 0) {
        try {
            Add-Content -Path $gi -Value (($faltam) -join "`r`n") -Encoding UTF8 -ErrorAction Stop
            Write-Log "GITIGNORE ${RepoPath}: adicionado $($faltam -join ', ')"
        } catch { Write-Log "GITIGNORE falhou em ${RepoPath}: $($_.Exception.Message)" }
    }
}

function Invoke-PushELimpeza {
    param([string]$Path, [string]$RepoKey, [bool]$DoPush, $Cfg)
    if (-not $DoPush) { return $null }
    $pushOut = git push 2>&1 | Out-String
    Write-Log "PUSH ${RepoKey}: $($pushOut.Trim())"
    if ($LASTEXITCODE -ne 0) { return 'PUSH_FALHOU' }
    if ($Cfg.modo -eq 'auto' -and $Cfg.limpeza_pos_push) {
        $resumoL = Invoke-Limpeza -RepoPath $Path -Cfg $Cfg
        Write-Log "LIMPEZA ${RepoKey}: $resumoL"
    }
    return $null
}

function Invoke-Limpeza {
    param([string]$RepoPath, $Cfg)
    $itens = @(
        [pscustomobject]@{ padrao='__pycache__'; tipo='pastas';   idade_dias=0; escopo='repo' },
        [pscustomobject]@{ padrao='*.pyc';       tipo='arquivos'; idade_dias=0; escopo='repo' },
        [pscustomobject]@{ padrao='*.log';       tipo='arquivos'; idade_dias=7; escopo='runtime' },
        [pscustomobject]@{ padrao='*';           tipo='arquivos'; idade_dias=3; escopo='temp-opencode' },
        [pscustomobject]@{ padrao='persistencia-*.lock'; tipo='arquivos'; idade_dias=0; escopo='temp-locks' }
    )
    if ($Cfg -and ($Cfg.PSObject.Properties.Name -contains 'limpeza_itens') -and $Cfg.limpeza_itens) {
        $itens = @($Cfg.limpeza_itens)
    }
    $apagados = 0; $bytes = [long]0
    foreach ($it in $itens) {
        $raizAlvo = $null
        if     ($it.escopo -eq 'repo')          { $raizAlvo = $RepoPath }
        elseif ($it.escopo -eq 'runtime')       { if (Test-Path "$RepoPath\runtime") { $raizAlvo = "$RepoPath\runtime" } }
        elseif ($it.escopo -eq 'temp-opencode') { $raizAlvo = Join-Path $env:TEMP 'opencode' }
        elseif ($it.escopo -eq 'temp-locks')    { $raizAlvo = $env:TEMP }
        if (-not $raizAlvo -or -not (Test-Path $raizAlvo)) { continue }
        $cutoff = (Get-Date).AddDays(-1 * [double]$it.idade_dias)
        if ($it.tipo -eq 'pastas') {
            $alvos = Get-ChildItem $raizAlvo -Recurse -Directory -Filter $it.padrao -ErrorAction SilentlyContinue
            foreach ($d in @($alvos)) {
                if ($d.LastWriteTime -gt $cutoff) { continue }
                $rel = ''
                if ($d.FullName.StartsWith($RepoPath)) { $rel = $d.FullName.Substring($RepoPath.Length).TrimStart('\','/') -replace '\\','/' }
                if (Test-ArquivoTrackeado -RepoPath $RepoPath -CaminhoRelativo $rel) { continue }
                try {
                    $sz = (Get-ChildItem $d.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
                    Remove-Item -LiteralPath $d.FullName -Recurse -Force -ErrorAction Stop
                    $apagados++; if ($sz) { $bytes += [long]$sz }
                } catch {
                    if ($_.Exception.Message -notmatch 'não existe|does not exist|n\u00e3o existe') { Write-Log "LIMPEZA: falha em $($d.FullName): $($_.Exception.Message)" }
                }
            }
        } else {
            $alvos = Get-ChildItem $raizAlvo -Recurse -File -Include $it.padrao -ErrorAction SilentlyContinue
            foreach ($f in @($alvos)) {
                if ($f.LastWriteTime -gt $cutoff) { continue }
                $rel = ''
                if ($f.FullName.StartsWith($RepoPath)) { $rel = $f.FullName.Substring($RepoPath.Length).TrimStart('\','/') -replace '\\','/' }
                if (Test-ArquivoTrackeado -RepoPath $RepoPath -CaminhoRelativo $rel) { continue }
                try {
                    Remove-Item -LiteralPath $f.FullName -Force -ErrorAction Stop
                    $apagados++; $bytes += [long]$f.Length
                } catch {
                    if ($_.Exception.Message -notmatch 'não existe|does not exist') { Write-Log "LIMPEZA: falha em $($f.FullName): $($_.Exception.Message)" }
                }
            }
        }
    }
    return '{0} itens, {1:N2} MB liberados' -f $apagados, ($bytes/1MB)
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
        foreach ($kv in @(@('ultimo_auto_commit',$null),@('debounce_minutos',30),@('preflight_codigo',$true),@('limpeza_pos_push',$true))) {
            if (-not ($cfg.PSObject.Properties.Name -contains $kv[0])) {
                $cfg | Add-Member -NotePropertyName $kv[0] -NotePropertyValue $kv[1] -Force
            }
        }
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
            $rPush = Invoke-PushELimpeza -Path $path -RepoKey $RepoKey -DoPush:$DoPush -Cfg $cfg
            Pop-Location; Remove-Item $lock -Force -ErrorAction SilentlyContinue
            if ($rPush) { return $rPush }
            return 'CLEAN'
        }

        # ---- politicas do modo AUTO (modo MANUAL mantem comportamento original) ----
        if ($cfg.modo -eq 'auto') {
            $codigos = @(); $vivos = 0
            foreach ($l in ($status -split "`n" | Where-Object { $_.Trim() })) {
                if ($l.Length -lt 4) { continue }
                $caminho = $l.Substring(3).Trim()
                $tipo = Get-TipoPendencia -Caminho $caminho -RepoPath $path
                if ($tipo -eq 'codigo') { $codigos += $caminho } else { $vivos++ }
            }
            # preflight minimo de codigo: quebrado nao sobe, vira snapshot recuperavel
            if ($codigos.Count -gt 0 -and $cfg.preflight_codigo) {
                $alvos = @($codigos | Where-Object { Test-Path (Join-Path $path $_) })
                $falhas = Test-PreFlightCodigo -RepoPath $path -Arquivos $alvos
                if ($falhas.Count -gt 0) {
                    # stash create ignora untracked: stage temporario para o snapshot pegar tudo
        git add -A 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Log "ADD ${RepoKey}: FALHOU (index.lock ou indice ocupado); ciclo abortado sem perda"
            Pop-Location; Remove-Item $lock -Force -ErrorAction SilentlyContinue
            return 'ADD_FALHOU'
        }
                    foreach ($ex in @($cfg.excluir)) { if ($ex) { git reset -q -- "$ex" 2>&1 | Out-Null } }
                    $snap = git stash create "[auto-wip] codigo quebrado: $($falhas -join ', ')"
                    git reset -q 2>&1 | Out-Null
                    if ($snap) { git stash store -m "[auto-wip $(Get-Date -Format 'yyyy-MM-dd HH:mm')] $($falhas -join ', ')" $snap | Out-Null }
                    Write-Log "AUTO WIP ${RepoKey}: preflight falhou ($($falhas -join ', ')); snapshot guardado, nada commitado"
                    Pop-Location; Remove-Item $lock -Force -ErrorAction SilentlyContinue
                    return 'WIP_QUEBRADO'
                }
            }
            # debounce: estado vivo sozinho espera o lote; codigo passa na hora
            if ($codigos.Count -eq 0 -and $cfg.ultimo_auto_commit) {
                try {
                    $dt = [datetime]::Parse($cfg.ultimo_auto_commit)
                    if (((Get-Date) - $dt).TotalMinutes -lt [double]$cfg.debounce_minutos) {
                        Pop-Location; Remove-Item $lock -Force -ErrorAction SilentlyContinue
                        return 'DEBOUNCE'
                    }
                } catch {}
            }
            # lixo estrutural nunca entra no espelho: garante o .gitignore antes do add
            Add-GitignoreLixo -RepoPath $path
        }

        git add -A 2>&1 | Out-Null
        foreach ($ex in @($cfg.excluir)) {
            if ($ex) { git reset -q -- "$ex" 2>&1 | Out-Null }
        }
        $msg = ''
        if ($UserMsg) { $msg = $UserMsg }
        else { $msg = "[gate] $MsgLabel - $(Get-Date -Format 'yyyy-MM-dd HH:mm')" }
        $commitOut = git commit -m $msg 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            Write-Log "COMMIT ${RepoKey}: FALHOU - $($commitOut.Trim())"
            Pop-Location; Remove-Item $lock -Force -ErrorAction SilentlyContinue
            return 'ERROR'
        }
        $commitHash = git rev-parse --short HEAD 2>$null
        Write-Log "COMMIT ${RepoKey}: $commitHash - $msg"
        if ($cfg.modo -eq 'auto') {
            $cfg | Add-Member -NotePropertyName ultimo_auto_commit -NotePropertyValue (Get-Date -Format 'o') -Force
            Set-Config $cfg
        }
        $rPush = Invoke-PushELimpeza -Path $path -RepoKey $RepoKey -DoPush:$DoPush -Cfg $cfg
        Pop-Location; Remove-Item $lock -Force -ErrorAction SilentlyContinue
        if ($rPush) { return $rPush }
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
