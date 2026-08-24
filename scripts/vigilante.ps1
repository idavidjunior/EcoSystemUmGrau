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
$quietPeriod = 900  # 15 min: so commita apos silencio no working tree (agrupa trabalho em lotes)
$maxInterval = 3600  # 1h: teto forcado - nunca ficar sem persistir, mesmo com atividade continua

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

# Quiet period: verifica se o working tree esta queto ha $quietPeriod segundos.
# Recebe o tempo desde a ultima sync (em segundos) para aplicar o teto forcado.
# Retorna $true se pode commitar (silencio) ou se o teto maximo foi atingido.
function Test-GitQuiet {
    param([string]$Path, [double]$SinceLastSync)
    $now = Get-Date

    # Teto forcado: mesmo com atividade continua, nunca passa mais de $maxInterval
    if ($SinceLastSync -ge $maxInterval) { return $true }

    # Procura o arquivo alterado mais recente no working tree
    $status = git -C $Path status --porcelain 2>$null
    if (-not $status) { return $true }
    $latestChange = [datetime]::MinValue
    foreach ($line in $status) {
        $file = $line.Substring(3).Trim()
        $full = Join-Path $Path $file
        if (Test-Path $full) {
            $lw = (Get-Item $full -ErrorAction SilentlyContinue).LastWriteTime
            if ($lw -gt $latestChange) { $latestChange = $lw }
        }
    }
    if ($latestChange -eq [datetime]::MinValue) { return $true }
    $idleSeconds = ($now - $latestChange).TotalSeconds
    return $idleSeconds -ge $quietPeriod
}

# Verifica se ha pendencias reais no working tree. Sem pendencias,
# mesmo passando os 15 minutos (ou 1h), nada e commitado.
function Test-GitPendente {
    param([string]$Path)
    $status = git -C $Path status --porcelain 2>$null
    return [bool]$status
}

function Sync-GitRepo {
    param([string]$Path, [string]$Label, [switch]$Push, [ref]$LastSync, [int]$Cooldown = $gitInterval)
    $now = Get-Date
    if (($now - $LastSync.Value).TotalSeconds -lt $Cooldown) { return $false }

    # Regra: sem pendencias, nao ha o que commitar. Nao chama o gate.
    if (-not (Test-GitPendente -Path $Path)) {
        $LastSync.Value = $now
        return $false
    }

    # Quiet period: so commita se o working tree estiver queto (ou teto forcado).
    # Evita commits no meio da atividade agrupando trabalho em lotes.
    $sinceLastSync = ($now - $LastSync.Value).TotalSeconds
    if (-not (Test-GitQuiet -Path $Path -SinceLastSync $sinceLastSync)) {
        Write-Log "Quiet period: repo $Label ainda em atividade, aguardando silencio."
        return $false
    }

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

    # Regra: sem pendencias, nao ha o que commitar. Nao chama o gate.
    if (-not (Test-GitPendente -Path $Path)) {
        $proj.LastSync = $now
        return
    }

    # Quiet period aplicado tambem aos projetos: agrupa salvamentos em lotes.
    $sinceLastSync = ($now - $proj.LastSync).TotalSeconds
    if (-not (Test-GitQuiet -Path $Path -SinceLastSync $sinceLastSync)) {
        Write-Log "Quiet period: projeto $($proj.Name) ainda em atividade, aguardando silencio."
        return
    }

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

# Memory decay diario: SUBSTITUIDO pelo SINAPSES VIVAS TIMER (fim do arquivo),
# cujo "sinapses.py ciclo" inclui decay + reindexacao + relatorio de saude.

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
# PREFERENCE DETECTOR: detecção automática de preferências do usuário (1x/h)
# ─────────────────────────────────────────────────────────────────────
# 3 abordagens: frase natural ("minha preferência é X"), repetição de uso, preditor de uso
$prefDetectTimer = New-Object System.Timers.Timer
$prefDetectTimer.Interval = 3600000  # check a cada 1h
$prefDetectTimer.AutoReset = $true
$lastPrefDetectDate = (Get-Date).Date.AddDays(-1)

$onPrefDetect = {
    $today = (Get-Date).Date
    if ($lastPrefDetectDate -lt $today) {
        $lastPrefDetectDate = $today
        Write-Log "PREF DETECTOR: varredura diária de preferências..."
        try {
            $result = python "$ecoDir\scripts\preference_detector.py" --run 2>&1 | Out-String
            Write-Log "PREF DETECTOR: $($result.Trim())"
        } catch { Write-Log "PREF DETECTOR: ignorado: $_" }
    }
}
Register-ObjectEvent $prefDetectTimer "Elapsed" -Action $onPrefDetect > $null
$prefDetectTimer.Start()

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

# ══════════════════════════════════════════════════════════════════════
# TRIAGEM TIMER: auditoria de organizacao (1x/dia) - move orfaos p/ _legado
# ══════════════════════════════════════════════════════════════════════
$triageTimer = New-Object System.Timers.Timer
$triageTimer.Interval = 3600000  # check a cada 1h
$triageTimer.AutoReset = $true
$lastTriageDate = (Get-Date).Date.AddDays(-1)  # roda no primeiro ciclo

$onTriage = {
    $today = (Get-Date).Date
    if ($lastTriageDate -lt $today) {
        $lastTriageDate = $today
        Write-Log "Triagem de organizacao diaria..."
        try {
            $out = python "$ecoDir\scripts\audit_triagem.py" --fix 2>&1 | Out-String
            $json = $out | ConvertFrom-Json -ErrorAction SilentlyContinue
            if ($json) {
                $movidos = @($json.movidos_legado)
                $artefatos = @($json.artefatos_git)
                if ($movidos.Count -gt 0) {
                    Write-Log "TRIAGEM: $($movidos.Count) orfaos movidos p/ _legado: $($movidos -join ', ')"
                } else {
                    Write-Log "TRIAGEM: nenhum orfao novo."
                }
                if ($artefatos.Count -gt 0) {
                    Write-Log "TRIAGEM: $($artefatos.Count) artefatos rastreados no git (revisar manualmente):"
                    $artefatos | ForEach-Object { Write-Log "TRIAGEM:   $($_.arquivo) ($($_.motivo))" }
                }
            } else {
                Write-Log "TRIAGEM: saida inesperada: $($out.Trim())"
            }
        } catch { Write-Log "Triagem ignorada: $_" }
    }
}
Register-ObjectEvent $triageTimer "Elapsed" -Action $onTriage > $null
$triageTimer.Start()

# ══════════════════════════════════════════════════════════════════════
# VOZ GUARDA TIMER: detecta regressao de paths temp fixos (audio) (2x/h)
# ══════════════════════════════════════════════════════════════════════
$vozGuardaTimer = New-Object System.Timers.Timer
$vozGuardaTimer.Interval = 1800000  # check a cada 30min
$vozGuardaTimer.AutoReset = $true

$onVozGuarda = {
    Write-Log "VOZ GUARDA: escaneando paths temp de audio..."
    try {
        $out = python "$ecoDir\scripts\voz_guarda.py" --check 2>&1 | Out-String
        $json = $out | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($json -and -not $json.ok) {
            $n = @($json.violacoes).Count
            if ($n -gt 0) {
                $v = @($json.violacoes)[0]
                Write-Log "VOZ GUARDA: VIOLACAO - $($v.arquivo):$($v.linha) $($v.fixado)"
            } else {
                Write-Log "VOZ GUARDA: VIOLACAO - speech_pipeline sem mkstemp"
            }
        } else {
            Write-Log "VOZ GUARDA: ok ($($json.arquivos_escaneados) arquivos, $($json.orphans_pendentes.Count) orfaos pendentes)"
        }
    } catch { Write-Log "VOZ GUARDA: scan ignorado: $_" }
}
Register-ObjectEvent $vozGuardaTimer "Elapsed" -Action $onVozGuarda > $null
$vozGuardaTimer.Start()

# BRIDGE HEALTH TIMER: verifica health da bridge a cada 2h, registra status
$bridgeHealthDir = "$ecoDir\connectivity\bridge\health"
$onBridgeHealth = {
    $bridgeHealthDir = "$ecoDir\connectivity\bridge\health"
    if (-not (Test-Path $bridgeHealthDir)) { New-Item -ItemType Directory -Path $bridgeHealthDir -Force | Out-Null }
    $ts = Get-Date -Format "yyyyMMdd_HHmmss"
    $bridgeOk = $false
    $serveOk = $false
    try {
        $b = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction Stop
        $bridgeOk = $true
    } catch {}
    try {
        $s = Get-NetTCPConnection -LocalPort 8767 -State Listen -ErrorAction Stop
        $serveOk = $true
    } catch {}
    $health = @{
        timestamp = (Get-Date).ToString("o")
        bridge_ok = $bridgeOk
        serve_ok = $serveOk
        all_healthy = ($bridgeOk -and $serveOk)
    } | ConvertTo-Json -Compress
    $healthFile = "$bridgeHealthDir\health_$ts.json"
    Set-Content -Path $healthFile -Value $health -Encoding UTF8
    # Cleanup: mantem apenas os 20 mais recentes
    $files = Get-ChildItem "$bridgeHealthDir\health_*.json" | Sort-Object Name -Descending
    if ($files.Count -gt 20) { $files | Select-Object -Skip 20 | Remove-Item -Force }
    if (-not $bridgeOk) { Write-Log "BRIDGE HEALTH: bridge (8765) DOWN" }
    if (-not $serveOk) { Write-Log "BRIDGE HEALTH: serve (8767) DOWN" }
}
$bridgeHealthTimer = New-Object System.Timers.Timer
$bridgeHealthTimer.Interval = 7200000  # 2h
$bridgeHealthTimer.AutoReset = $true
Register-ObjectEvent $bridgeHealthTimer "Elapsed" -Action $onBridgeHealth > $null
$bridgeHealthTimer.Start()

# INTEGRITY GUARD TIMER: verifica e corrige mojibake/truncamento em JSON (1x/h)
$integrityTimer = New-Object System.Timers.Timer
$integrityTimer.Interval = 3600000  # 1h
$integrityTimer.AutoReset = $true

$onIntegrity = {
    Write-Log "INTEGRITY: verificando dados (mojibake/truncamento)..."
    try {
        $out = python "$ecoDir\scripts\integrity_guard.py" --fix 2>&1 | Out-String
        if ($out -match 'RESULTADO: 0 arquivo') {
            Write-Log "INTEGRITY: ok (nenhuma corrupção)"
        } else {
            $m = [regex]::Match($out, 'RESULTADO: (\d+) string')
            if ($m.Success) {
                $n = $m.Groups[1].Value
                $arqs = ([regex]::Matches($out, 'CORRIGIDO')).Count
                Write-Log "INTEGRITY: $n string(s) corrigida(s) em $arqs arquivo(s) (backup em runtime\backups\integrity_guard)"
                python "$ecoDir\scripts\memory_engine.py" log "integrity-guard: $n strings de mojibake corrigidas automaticamente" 2>$null
            } else {
                Write-Log "INTEGRITY: $($out.Trim())"
            }
        }
    } catch { Write-Log "INTEGRITY: scan ignorado: $_" }
}
Register-ObjectEvent $integrityTimer "Elapsed" -Action $onIntegrity > $null
$integrityTimer.Start()

# ���������������������������������������������������������������������������������������������������������������������������������������������
# OPENCODE CACHE TIMER: limpeza de logs antigos/oversized (1x/h, alinhado ao maxInterval)
# ���������������������������������������������������������������������������������������������������������������������������������������������
$opencodeCacheTimer = New-Object System.Timers.Timer
$opencodeCacheTimer.Interval = 3600000  # 1h = maxInterval
$opencodeCacheTimer.AutoReset = $true

$onOpencodeCache = {
    Write-Log "OPENCODE CACHE: verificando/limpando logs..."
    try {
        $out = python "$ecoDir\scripts\monitor_opencode_cache.py" --clean 2>&1 | Out-String
        $out.Trim() | ForEach-Object { Write-Log "  $_" }
    } catch { Write-Log "OPENCODE CACHE: ignorado: $_" }
}
Register-ObjectEvent $opencodeCacheTimer "Elapsed" -Action $onOpencodeCache > $null
$opencodeCacheTimer.Start()

# ══════════════════════════════════════════════════════════════════════
# EVOLUTION RADAR TIMER: auto-evolução curada (4h, permissão admin, pacotes)
# ══════════════════════════════════════════════════════════════════════
$evolutionRadarInterval = 14400000  # 4h (configurável)
$evolutionRadarTimer = New-Object System.Timers.Timer
$evolutionRadarTimer.Interval = $evolutionRadarInterval
$evolutionRadarTimer.AutoReset = $true

$onEvolutionRadar = {
    # Permissão de administrador obrigatória
    if (-not (Test-Path "$ecoDir\.evolution_admin_ok") -and $env:EVOLUTION_RADAR_ADMIN -ne "1") {
        Write-Log "EVOLUTION RADAR: sem permissão admin (EVOLUTION_RADAR_ADMIN=1 ou .evolution_admin_ok), pulando."
        return
    }
    Write-Log "EVOLUTION RADAR: iniciando ciclo (collect -> filter -> package)..."
    try {
        $out = python "$ecoDir\scripts\evolution_radar_collect.py" --full 2>&1 | Out-String
        $out.Trim() | ForEach-Object { Write-Log "  $_" }

        # Verifica se gerou pacote e notifica admin
        $packDir = "$ecoDir\conhecimento\evolution-radar\pacotes"
        if (Test-Path $packDir) {
            $pack = Get-ChildItem $packDir -Filter "evolution-pack-*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($pack) {
                $packData = Get-Content $pack.FullName -Raw | ConvertFrom-Json -ErrorAction SilentlyContinue
                if ($packData -and $packData.proposals) {
                    $count = $packData.proposals.Count
                    $msg = "Evolution Radar: pacote $($pack.BaseName) pronto com $count proposta(s). Aplicar?"
                    Write-Log "EVOLUTION RADAR: $msg"
                    # Notifica via bridge (TTS/texto)
                    python "$ecoDir\scripts\jarvis_bridge.py" notify "$msg" 2>$null
                }
            }
        }
    } catch { Write-Log "EVOLUTION RADAR: erro: $_" }
}
Register-ObjectEvent $evolutionRadarTimer "Elapsed" -Action $onEvolutionRadar > $null
$evolutionRadarTimer.Start()

# ═══════════════════════════════════════════════════════════════════════
# CLEANUP TIMERS: limpeza interna do ecossistema (sem afetar memória/consistência)
# ══════════════════════════════════════════════════════════════════════

# State backups: mantém últimos 10 (1x/dia)
$stateBackupTimer = New-Object System.Timers.Timer
$stateBackupTimer.Interval = 86400000  # 24h
$stateBackupTimer.AutoReset = $true
$onStateBackup = {
    Write-Log "STATE BACKUP CLEANUP: verificando backups antigos..."
    try {
        $out = python "$ecoDir\scripts\cleanup_state_backups.py" --keep 10 2>&1 | Out-String
        $out.Trim() | ForEach-Object { Write-Log "  $_" }
    } catch { Write-Log "STATE BACKUP CLEANUP: ignorado: $_" }
}
Register-ObjectEvent $stateBackupTimer "Elapsed" -Action $onStateBackup > $null
$stateBackupTimer.Start()

# Knowledge graph: mantém últimos 2 (1x/dia)
$graphCleanupTimer = New-Object System.Timers.Timer
$graphCleanupTimer.Interval = 86400000  # 24h
$graphCleanupTimer.AutoReset = $true
$onGraphCleanup = {
    Write-Log "KNOWLEDGE GRAPH CLEANUP: rotacionando grafos..."
    try {
        $out = python "$ecoDir\scripts\cleanup_knowledge_graph.py" --keep 2 2>&1 | Out-String
        $out.Trim() | ForEach-Object { Write-Log "  $_" }
    } catch { Write-Log "KNOWLEDGE GRAPH CLEANUP: ignorado: $_" }
}
Register-ObjectEvent $graphCleanupTimer "Elapsed" -Action $onGraphCleanup > $null
$graphCleanupTimer.Start()

# Ecosystem logs: >30 dias ou >100MB total (1x/dia)
$ecoLogsTimer = New-Object System.Timers.Timer
$ecoLogsTimer.Interval = 86400000  # 24h
$ecoLogsTimer.AutoReset = $true
$onEcoLogs = {
    Write-Log "ECOSYSTEM LOGS CLEANUP: limpando logs antigos..."
    try {
        $out = python "$ecoDir\scripts\cleanup_ecosystem_logs.py" --max-age-days 30 --max-mb 100 2>&1 | Out-String
        $out.Trim() | ForEach-Object { Write-Log "  $_" }
    } catch { Write-Log "ECOSYSTEM LOGS CLEANUP: ignorado: $_" }
}
Register-ObjectEvent $ecoLogsTimer "Elapsed" -Action $onEcoLogs > $null
$ecoLogsTimer.Start()

# Evolution Radar raw: mantém últimos 5 (1x/dia)
$radarRawTimer = New-Object System.Timers.Timer
$radarRawTimer.Interval = 86400000  # 24h
$radarRawTimer.AutoReset = $true
$onRadarRaw = {
    Write-Log "RADAR RAW CLEANUP: limpando JSONL brutos antigos..."
    try {
        $out = python "$ecoDir\scripts\cleanup_radar_raw.py" --keep 5 2>&1 | Out-String
        $out.Trim() | ForEach-Object { Write-Log "  $_" }
    } catch { Write-Log "RADAR RAW CLEANUP: ignorado: $_" }
}
Register-ObjectEvent $radarRawTimer "Elapsed" -Action $onRadarRaw > $null
$radarRawTimer.Start()

# SYSTEM GUARDIAN TIMER: garante que system_guardian.py esta rodando (check a cada 5min)
$guardianPidFile = "$PSScriptRoot\guardian.pid"
$guardianScript = "$PSScriptRoot\system_guardian.py"
$onGuardianCheck = {
    $guardianPidFile = "$PSScriptRoot\guardian.pid"
    $running = $false
    if (Test-Path $guardianPidFile) {
        $gpid = Get-Content $guardianPidFile -ErrorAction SilentlyContinue
        if ($gpid -and (Get-Process -Id $gpid -ErrorAction SilentlyContinue)) { $running = $true }
    }
    if (-not $running) {
        $procs = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
            (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine -like "*system_guardian*"
        }
        if ($procs) { $running = $true }
    }
    if (-not $running) {
        try {
            Start-Process python -ArgumentList "`"$PSScriptRoot\system_guardian.py`"" -WindowStyle Hidden
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] System Guardian iniciado pelo vigilantе"
        } catch {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ERRO ao iniciar System Guardian: $($_.Exception.Message)"
        }
    }
}
$guardianTimer = New-Object System.Timers.Timer
$guardianTimer.Interval = 300000  # 5min
$guardianTimer.AutoReset = $true
Register-ObjectEvent $guardianTimer "Elapsed" -Action $onGuardianCheck > $null
$guardianTimer.Start()
# Start guardian immediately on vigilante boot
try {
    if (-not (Test-Path $guardianPidFile)) {
        Start-Process python -ArgumentList "`"$guardianScript`"" -WindowStyle Hidden
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] System Guardian iniciado no boot do vigilantе"
    }
} catch {}

# ARCHITECTURE INTEGRITY TIMER: verifica saude estrutural completa do ecossistema (1x/4h)
$onArchIntegrity = {
    Write-Log "ARCH INTEGRITY: rodando monitor de integridade arquitetural..."
    try {
        $out = python "$ecoDir\scripts\architecture_integrity_monitor.py" --json 2>&1 | Out-String
        $result = $out | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($result) {
            $s = $result.summary
            Write-Log "ARCH INTEGRITY: $($s.total) checks - PASS:$($s.pass) WARN:$($s.warn) FAIL:$($s.fail)"
            if ($s.fail -gt 0) {
                $fails = $result.checks | Where-Object { $_.status -eq "FAIL" }
                foreach ($f in $fails) {
                    Write-Log "ARCH INTEGRITY FAIL: $($f.name) - $($f.detail)"
                }
            }
            if ($result.fixes.Count -gt 0) {
                foreach ($fx in $result.fixes) {
                    Write-Log "ARCH INTEGRITY FIX: $fx"
                }
            }
        }
    } catch { Write-Log "ARCH INTEGRITY: erro: $_" }
}
$archIntegrityTimer = New-Object System.Timers.Timer
$archIntegrityTimer.Interval = 14400000  # 4h
$archIntegrityTimer.AutoReset = $true
Register-ObjectEvent $archIntegrityTimer "Elapsed" -Action $onArchIntegrity > $null
$archIntegrityTimer.Start()

# SINAPSES VIVAS: molde canonico do vigilante (mesmo padrao comprovado do
# LEARN TIMER): timer de evento + flag de data. Gate 24h persistido no
# marcador runtime/sinapses/ultimo_ciclo.txt.
$sinapsesMarcador = "$ecoDir\runtime\sinapses\ultimo_ciclo.txt"
$lastSinapsesRun = if (Test-Path $sinapsesMarcador) {
    (Get-Item $sinapsesMarcador).LastWriteTime
} else { [datetime]::MinValue }

$onSinapsesCiclo = {
    try {
        $marcador = "$ecoDir\runtime\sinapses\ultimo_ciclo.txt"
        $ultima = if (Test-Path $marcador) { (Get-Item $marcador).LastWriteTime }
                  else { [datetime]::MinValue }
        if (((Get-Date) - $ultima).TotalHours -lt 24) { return }
        Write-Log "SINAPSES: destilacao de lacunas iniciando..."
        $outD = python "$ecoDir\scripts\sinapses.py" destilar 2>&1 | Out-String
        Write-Log ("SINAPSES destilar: " + ($outD.Trim() -replace '\r?\n', ' | '))
        Write-Log "SINAPSES: ciclo de vida iniciando (decay + reindex + relatorio)..."
        $out = python "$ecoDir\scripts\sinapses.py" ciclo 2>&1 | Out-String
        $resumo = ($out -split "`n" | Where-Object { $_ -match "memorias ativas|arquivadas" }) -join "; "
        Write-Log "SINAPSES: $resumo"
        Set-Content -Path $marcador -Value (Get-Date).ToString('o') -Encoding UTF8
    } catch { Write-Log "SINAPSES: erro: $_" }
}
$sinapsesTimer = New-Object System.Timers.Timer
$sinapsesTimer.Interval = 3600000   # checa a cada 1h; gate interno de 24h
$sinapsesTimer.AutoReset = $true
Register-ObjectEvent $sinapsesTimer "Elapsed" -Action $onSinapsesCiclo > $null
$sinapsesTimer.Start()

# Mantem vivo
while ($true) { Start-Sleep -Seconds 10 }
