param(
    [switch]$Stop,
    [switch]$Status,
    [switch]$Foreground
)

$ErrorActionPreference = "Continue"
$scriptLabel = "[Vigilante]"
$pidFile = "$env:USERPROFILE\.vigilante.pid"
$logFile = "$env:USERPROFILE\.vigilante.log"
$ecoDir = "C:\Users\Playtec-bancada\Desktop\Codigos\EcoSystemUmGrau"
$lerDir = "$ecoDir\ler-runtime"
$learnDir = "$ecoDir\conhecimento\aprendizados"
$gitInterval = 300  # 5 min entre git sync

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
        } catch { Write-Log "ERRO: $_" }
    }
}

# Registrar eventos
Register-ObjectEvent $watcher "Created" -Action $onEvent > $null
Register-ObjectEvent $watcher "Changed" -Action $onEvent > $null
Register-ObjectEvent $debounce "Elapsed" -Action $onDebounce > $null

# ══════════════════════════════════════════════════════════════════════
# GIT SYNC: Push + Pull automatico (5 min)
# ══════════════════════════════════════════════════════════════════════
$ecoLastSync = [datetime]::MinValue
$lerLastSync = [datetime]::MinValue

function Sync-GitRepo {
    param([string]$Path, [string]$Label, [switch]$Push, [ref]$LastSync)
    $now = Get-Date
    if (($now - $LastSync.Value).TotalSeconds -lt $gitInterval) { return }

    try {
        Push-Location $Path -ErrorAction Stop

        # PULL primeiro (traz mudancas remotas)
        if ($Push) {
            $pullOut = git pull --ff-only 2>&1
            if ($LASTEXITCODE -eq 0 -and $pullOut -match "Fast-forward|Updating") {
                Write-Log "Git pull ($Label): ${pullOut}"
            }
        }

        # Depois COMMIT + PUSH (se houver mudancas locais)
        $status = git status --porcelain 2>&1 | Out-String
        if ($status.Trim()) {
            git add -A 2>&1 | Out-Null
            $dateStr = Get-Date -Format "yyyy-MM-dd HH:mm"
            git commit -m "[auto] $Label - $dateStr" 2>&1 | Out-Null
            if ($Push) {
                $pushOut = git push 2>&1
                Write-Log "Git sync ($Label): commit + push OK"
            } else {
                Write-Log "Git sync ($Label): commit local OK"
            }
        }

        Pop-Location
        $LastSync.Value = $now
    } catch { Write-Log "Git sync ($Label) ignorado: $_" }
}

Write-Log "Vigilante pronto (FSW + git sync a cada ${gitInterval}s)"

# ══════════════════════════════════════════════════════════════════════
# LOOP PRINCIPAL: timer de sincronizacao git
# ══════════════════════════════════════════════════════════════════════
$gitTimer = New-Object System.Timers.Timer
$gitTimer.Interval = 30000  # check a cada 30s (mas so executa a cada 300s)
$gitTimer.AutoReset = $true

$onGitSync = {
    Sync-GitRepo -Path $ecoDir -Label "EcoSystemUmGrau" -Push -LastSync ([ref]$ecoLastSync)
    Sync-GitRepo -Path $lerDir -Label "LER" -LastSync ([ref]$lerLastSync)
}

Register-ObjectEvent $gitTimer "Elapsed" -Action $onGitSync > $null
$gitTimer.Start()

# Mantem vivo
while ($true) { Start-Sleep -Seconds 10 }
