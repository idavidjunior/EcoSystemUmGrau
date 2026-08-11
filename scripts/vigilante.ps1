param(
    [switch]$Stop,
    [switch]$Status,
    [switch]$Foreground
)

$ErrorActionPreference = "Continue"
$scriptLabel = "[Vigilante]"
$pidFile = "$env:USERPROFILE\.vigilante.pid"
$logFile = "$env:USERPROFILE\.vigilante.log"
$ecoDir = Split-Path $PSScriptRoot -Parent
$lerDir = "$ecoDir\ler-runtime"
$learnDir = "$ecoDir\conhecimento\aprendizados"
$projectsDir = "$env:USERPROFILE\Documents\Default Project"
$gitInterval = 300  # 5 min entre git sync (eco/ler)
$projectGitInterval = 60  # 1 min entre git sync para projetos (menor = mais responsivo)

# Auto-descoberta de projetos Android com git remote
# EXCLUI o proprio EcoSystemUmGrau (repo principal) e ler-runtime (sem remote)
$projectRepos = @()
if (Test-Path $projectsDir) {
    Get-ChildItem $projectsDir -Directory | Where-Object {
        $remote = git -C $_.FullName remote -v 2>&1 | Where-Object { $_ -match "fetch" }
        $remote -and (Test-Path "$($_.FullName)\.git") -and
        $_.FullName -ne $ecoDir -and $_.Name -ne "ler-runtime"
    } | ForEach-Object { $projectRepos += @{Path=$_.FullName; Name=$_.Name; LastSync=[datetime]::MinValue} }
}

function Write-Log {
    param($Msg)
    $line = "[$(Get-Date -Format 'HH:mm:ss')] $Msg"
    try { Add-Content -Path $logFile -Value $line -Encoding UTF8 -ErrorAction Stop } catch {}
    if ($Foreground) { Write-Host "$scriptLabel $line" } else { Write-Host "$scriptLabel $line" }
}

# ─── Stop ──────────────────────────────────────────────────────────────
if ($Stop) {
    if (Test-Path $pidFile) {
        $savedPid = (Get-Content $pidFile -Raw).Trim()
        try { Stop-Process -Id $savedPid -Force -ErrorAction SilentlyContinue; Write-Host "$scriptLabel Processo $savedPid parado." } catch {}
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    } else { Write-Host "$scriptLabel Nenhum processo ativo." }
    return
}

# ─── Status ────────────────────────────────────────────────────────────
if ($Status) {
    if (Test-Path $pidFile) {
        $savedPid = (Get-Content $pidFile -Raw).Trim()
        $proc = Get-Process -Id $savedPid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "$scriptLabel ATIVO (PID $savedPid)" -ForegroundColor Green
            if (Test-Path $logFile) { Get-Content $logFile -Tail 6 }
        } else {
            Write-Host "$scriptLabel PID $savedPid encontrado mas morto." -ForegroundColor Yellow
            Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
        }
    } else { Write-Host "$scriptLabel INATIVO" -ForegroundColor Yellow }
    return
}

# ─── Prevent duplicate ─────────────────────────────────────────────────
$myPid = [System.Diagnostics.Process]::GetCurrentProcess().Id
if (Test-Path $pidFile) {
    $oldPid = (Get-Content $pidFile -Raw).Trim()
    $oldProc = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
    if ($oldProc) { Write-Host "$scriptLabel Ja rodando (PID $oldPid). Use -Stop primeiro." -ForegroundColor Yellow; return }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}
$myPid | Out-File $pidFile -Encoding UTF8 -Force

$env:PYTHONPATH = "$lerDir;$env:PYTHONPATH"
if (-not (Test-Path $learnDir)) { New-Item -ItemType Directory -Path $learnDir -Force | Out-Null }

Write-Log "=== VIGILANTE INICIADO (PID $myPid) ==="
Write-Log "Eco: $ecoDir | LER: $lerDir"

# ══════════════════════════════════════════════════════════════════════
# WATCHER: FileSystemWatcher para aprendizado (tempo real, sem polling)
# ══════════════════════════════════════════════════════════════════════
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $learnDir
$watcher.Filter = "*.md"
$watcher.IncludeSubdirectories = $false
$watcher.EnableRaisingEvents = $true

# Timer de debounce (300ms) para evitar multiplos eventos no mesmo arquivo
$debounce = New-Object System.Timers.Timer
$debounce.Interval = 300
$debounce.AutoReset = $false
$pendingFiles = New-Object System.Collections.Generic.List[string]

$onEvent = {
    $path = $Event.SourceArgs[1].FullPath
    $pendingFiles.Add($path)
    $debounce.Stop()
    $debounce.Start()
}

$onDebounce = {
    $debounce.Stop()
    $unique = $pendingFiles.ToArray() | Select-Object -Unique
    $pendingFiles.Clear()
    $graphUpdated = $false
    foreach ($file in $unique) {
        if (-not (Test-Path $file)) { continue }
        $fileName = Split-Path $file -Leaf
        Write-Log "Novo aprendizado: $fileName"
        try {
            $python = @"
import sys, os
sys.path.insert(0, r'$lerDir')
from agent.knowledge_consolidator import register_learning
with open(r'$file', encoding='utf-8') as f: register_learning(r'$file')
print('OK')
"@
            $result = python -c $python 2>&1
            Write-Log "Consolidator: $result"
            $graphUpdated = $true
        } catch { Write-Log "ERRO: $_" }
    }
    if ($graphUpdated) {
        try {
            $output = python "$ecoDir\scripts\generate-obsidian-notes.py" 2>&1
            Write-Log "Obsidian notes: $output"
        } catch { Write-Log "Obsidian notes ignorado: $_" }
    }

    # Pre-flight check: validar config se houve mudanca no template
    $templatePath = "$ecoDir\config\opencode.jsonc"
    $templateChanged = (Get-Item $templatePath -ErrorAction SilentlyContinue).LastWriteTime
    if ($templateChanged -and ((Get-Date) - $templateChanged).TotalSeconds -lt 600) {
        Write-Log "Template alterado recentemente. Executando pre-flight..."
        try {
            $result = python "$ecoDir\scripts\preflight_check.py" 2>&1
            Write-Log "Pre-flight: $result"
        } catch { Write-Log "Pre-flight ignorado: $_" }
    }
}

# Registrar eventos
Register-ObjectEvent $watcher "Created" -Action $onEvent > $null
Register-ObjectEvent $watcher "Changed" -Action $onEvent > $null
Register-ObjectEvent $debounce "Elapsed" -Action $onDebounce > $null

# ══════════════════════════════════════════════════════════════════════
# PROJECT WATCHERS: FileSystemWatcher para cada repo Android
# ══════════════════════════════════════════════════════════════════════
$projectDebounceMs = 3000  # 3s para agrupar salvamentos consecutivos
$projectPending = New-Object System.Collections.Generic.List[string]

$projectDebounceTimer = New-Object System.Timers.Timer
$projectDebounceTimer.Interval = $projectDebounceMs
$projectDebounceTimer.AutoReset = $false

$onProjectEvent = {
    $path = $Event.SourceArgs[1].FullPath
    $repopath = $Event.MessageData  # path do repo passado como MessageData
    $idx = [array]::IndexOf($projectRepos.Path, $repopath)
    if ($idx -ge 0) {
        if (-not $projectPending.Contains($repopath)) { $projectPending.Add($repopath) }
        $projectDebounceTimer.Stop(); $projectDebounceTimer.Start()
    }
}

$onProjectDebounce = {
    $projectDebounceTimer.Stop()
    $unique = $projectPending.ToArray() | Select-Object -Unique
    $projectPending.Clear()
    foreach ($repoPath in $unique) {
        Write-Log "Mudanca detectada em: $(Split-Path $repoPath -Leaf)"
        Sync-ProjectRepo -Path $repoPath -Force
    }
}

Register-ObjectEvent $projectDebounceTimer "Elapsed" -Action $onProjectDebounce > $null

# Configurar watcher para cada projeto
$projectExtensions = @("*.kt", "*.java", "*.py", "*.xml", "*.json", "*.ps1", "*.bat", "*.md", "*.gradle", "*.properties")
foreach ($proj in $projectRepos) {
    try {
        $w = New-Object System.IO.FileSystemWatcher
        $w.Path = $proj.Path
        $w.IncludeSubdirectories = $true
        $w.NotifyFilter = [System.IO.NotifyFilters]::FileName -bor [System.IO.NotifyFilters]::LastWrite -bor [System.IO.NotifyFilters]::DirectoryName
        $w.EnableRaisingEvents = $true
        # filtro: Created/Changed pra cada extensao
        Register-ObjectEvent $w "Created" -MessageData $proj.Path -Action $onProjectEvent > $null
        Register-ObjectEvent $w "Changed" -MessageData $proj.Path -Action $onProjectEvent > $null
        Register-ObjectEvent $w "Deleted" -MessageData $proj.Path -Action $onProjectEvent > $null
        Register-ObjectEvent $w "Renamed" -MessageData $proj.Path -Action $onProjectEvent > $null
        Write-Log "Watcher: $($proj.Name)"
    } catch { Write-Log "Watcher $($proj.Name) ignorado: $_" }
}

# ══════════════════════════════════════════════════════════════════════
# GIT SYNC: Push + Pull automatico (5 min eco/ler, 1 min projetos)
# ══════════════════════════════════════════════════════════════════════
$ecoLastSync = [datetime]::MinValue
$lerLastSync = [datetime]::MinValue
$lastLearnDate = (Get-Date).Date.AddDays(-1)  # roda no primeiro ciclo

function Sync-GitRepo {
    param([string]$Path, [string]$Label, [switch]$Push, [ref]$LastSync, [int]$Cooldown = $gitInterval)
    $now = Get-Date
    if (($now - $LastSync.Value).TotalSeconds -lt $Cooldown) { return $false }

    # PONTO UNICO DE PERSISTENCIA: todo commit/push passa pelo gate.
    # Em modo manual, o gate retem as pendencias (nada e commitado).
    & "$PSScriptRoot\persistencia.ps1" run-sync -Repo $Path -Label $Label -Push:$Push | Out-Null
    $LastSync.Value = $now
    return $true
}

# Sincroniza um repo de projeto Android (pull + commit + push)
function Sync-ProjectRepo {
    param([string]$Path, [switch]$Force)
    $proj = $projectRepos | Where-Object { $_.Path -eq $Path }
    if (-not $proj) { return }
    $now = Get-Date
    if (-not $Force -and ($now - $proj.LastSync).TotalSeconds -lt $projectGitInterval) { return }

    # PONTO UNICO DE PERSISTENCIA: mesmo gate usado para projetos Android
    & "$PSScriptRoot\persistencia.ps1" run-sync -Repo $Path -Label "Android/$($proj.Name)" -Push | Out-Null
    $proj.LastSync = $now
}

Write-Log "Vigilante pronto (FSW + git sync a cada ${gitInterval}s)"
if ($projectRepos.Count -gt 0) {
    Write-Log "Vigilante monitora $($projectRepos.Count) projetos: $(($projectRepos.Name) -join ', ')"
}

# ══════════════════════════════════════════════════════════════════════
# LOOP PRINCIPAL: timer de sincronizacao git
# ══════════════════════════════════════════════════════════════════════
$gitTimer = New-Object System.Timers.Timer
$gitTimer.Interval = 30000  # check a cada 30s
$gitTimer.AutoReset = $true

$onGitSync = {
    $changed = Sync-GitRepo -Path $ecoDir -Label "EcoSystemUmGrau" -Push -LastSync ([ref]$ecoLastSync)
    Sync-GitRepo -Path $lerDir -Label "LER" -LastSync ([ref]$lerLastSync)
    # ATENCAO (fix loop infinito 2026-08-08): NAO logar git-sync aqui.
    # memory_engine log escreve em conhecimento/memoria/sessions/*.jsonl (dentro do repo),
    # o que re-dispara o FileSystemWatcher -> novo push -> novo log -> loop infinito.
    # Sincroniza projetos Android (cada um tem seu proprio cooldown)
    foreach ($proj in $projectRepos) {
        $lastRef = [ref]$proj.LastSync
        $projName = $proj.Name
        $projChanged = Sync-GitRepo -Path $proj.Path -Label "Android/$projName" -Push -LastSync $lastRef -Cooldown $projectGitInterval
    }
}

Register-ObjectEvent $gitTimer "Elapsed" -Action $onGitSync > $null
$gitTimer.Start()

# Memory decay pass diario
$decayTimer = New-Object System.Timers.Timer
$decayTimer.Interval = 86400000  # 24h
$decayTimer.AutoReset = $true
$onDecay = { python "$ecoDir\scripts\memory_engine.py" decay 2>$null | Out-Null }
Register-ObjectEvent $decayTimer "Elapsed" -Action $onDecay > $null
$decayTimer.Start()

# ══════════════════════════════════════════════════════════════════════
# LEARN TIMER: varredura proativa uma vez por dia
# ══════════════════════════════════════════════════════════════════════
$learnTimer = New-Object System.Timers.Timer
$learnTimer.Interval = 3600000  # check a cada 1h
$learnTimer.AutoReset = $true

$onLearn = {
    $today = (Get-Date).Date
    if ($lastLearnDate -lt $today) {
        $lastLearnDate = $today
        Write-Log "Varredura proativa diaria..."
        try {
            $result = & "$ecoDir\scripts\ecosystem.ps1" learn 2>&1 | Out-String
            Write-Log "Learn: $($result.Trim())"
            # Regenera notas do Obsidian apos learn
            $output = python "$ecoDir\scripts\generate-obsidian-notes.py" 2>&1
            Write-Log "Obsidian notes: $output"
        } catch { Write-Log "Learn ignorado: $_" }
    }
}
Register-ObjectEvent $learnTimer "Elapsed" -Action $onLearn > $null
$learnTimer.Start()

# ══════════════════════════════════════════════════════════════════════
# RULES TIMER: verifica consistencia das 3 camadas de regras (1x/h)
# ══════════════════════════════════════════════════════════════════════
$rulesTimer = New-Object System.Timers.Timer
$rulesTimer.Interval = 3600000  # 1h
$rulesTimer.AutoReset = $true

$onRulesCheck = {
    try {
        $rulesOut = python "$ecoDir\scripts\sync_rules.py" check 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            Write-Log "REGRA IGNORADA/NAO SINCRONIZADA:"
            $rulesOut -split "`n" | Where-Object { $_ -match "DIVERGENCIA" } | ForEach-Object { Write-Log "  $_" }
            try {
                python "$ecoDir\scripts\memory_engine.py" log "rules-divergencia: alguma regra nao sincronizada entre as 3 camadas" 2>$null
            } catch {}
        }
    } catch { Write-Log "Rules check ignorado: $_" }
}
Register-ObjectEvent $rulesTimer "Elapsed" -Action $onRulesCheck > $null
$rulesTimer.Start()

# Mantem vivo
while ($true) { Start-Sleep -Seconds 10 }
