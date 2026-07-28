param(
    [switch]$Stop,
    [switch]$Status
)

$ErrorActionPreference = "Continue"
$scriptLabel = "[Vigilante]"
$pidFilePath = "$env:USERPROFILE\.vigilante.pid"
$logFilePath = "$env:USERPROFILE\.vigilante.log"
$learnDir = "C:\Users\Playtec-bancada\Desktop\Codigos\EcoSystemUmGrau\conhecimento\aprendizados"
$ecoDir = "C:\Users\Playtec-bancada\Desktop\Codigos\EcoSystemUmGrau"
$lerDir = "C:\Users\Playtec-bancada\.ler"
$lerBase = $lerDir

function Write-Log {
    param($Msg)
    $line = "[$(Get-Date -Format 'HH:mm:ss')] $Msg"
    try { Add-Content -Path $logFilePath -Value $line -Encoding UTF8 -ErrorAction Stop } catch {}
    Write-Host "$scriptLabel $line"
}

# ─── Stop ──────────────────────────────────────────────────────────────
if ($Stop) {
    if (Test-Path $pidFilePath) {
        $savedPid = Get-Content $pidFilePath -Raw
        if ($savedPid) {
            $savedPid = $savedPid.Trim()
            try { Stop-Process -Id $savedPid -Force -ErrorAction SilentlyContinue } catch {}
            Write-Host "$scriptLabel Processo $savedPid parado."
        }
        Remove-Item $pidFilePath -Force -ErrorAction SilentlyContinue
    } else {
        Write-Host "$scriptLabel Nenhum processo ativo."
    }
    return
}

# ─── Status ────────────────────────────────────────────────────────────
if ($Status) {
    if (Test-Path $pidFilePath) {
        $savedPid = (Get-Content $pidFilePath -Raw).Trim()
        $proc = Get-Process -Id $savedPid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "$scriptLabel ATIVO (PID $savedPid)" -ForegroundColor Green
            if (Test-Path $logFilePath) { Get-Content $logFilePath -Tail 5 }
        } else {
            Write-Host "$scriptLabel PID $savedPid encontrado mas processo morto." -ForegroundColor Yellow
            Remove-Item $pidFilePath -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "$scriptLabel INATIVO" -ForegroundColor Yellow
    }
    return
}

# ─── Prevent duplicate ─────────────────────────────────────────────────
$myPid = [System.Diagnostics.Process]::GetCurrentProcess().Id
if (Test-Path $pidFilePath) {
    $oldPid = (Get-Content $pidFilePath -Raw).Trim()
    $oldProc = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
    if ($oldProc) {
        Write-Host "$scriptLabel Ja esta rodando (PID $oldPid). Use -Stop primeiro." -ForegroundColor Yellow
        return
    }
    Remove-Item $pidFilePath -Force -ErrorAction SilentlyContinue
}
$myPid | Out-File $pidFilePath -Encoding UTF8 -Force

Write-Log "=== VIGILANTE INICIADO (PID $myPid) ==="
Write-Log "Monitorando: $learnDir"
Write-Log "LER: $lerBase"

$env:PYTHONPATH = "$lerBase;$env:PYTHONPATH"

# ─── Ensure dirs exist ────────────────────────────────────────────────
if (-not (Test-Path $learnDir)) { New-Item -ItemType Directory -Path $learnDir -Force | Out-Null }

# ─── Polling state ──────────────────────────────────────────────────────
$knownHashes = @{}
$ecoGitSyncFile = "$env:USERPROFILE\.vigilante.gitsync.eco"
$lerGitSyncFile = "$env:USERPROFILE\.vigilante.gitsync.ler"
$pollInterval = 30      # segundos entre polls
$gitInterval = 300      # 5 min entre git sync
$debounceSeconds = 3    # aguarda estabilizacao do arquivo

function Invoke-Register {
    param($FilePath)
    if (-not (Test-Path $FilePath)) { return }
    $fileName = Split-Path $FilePath -Leaf
    Write-Log "Novo aprendizado: $fileName"

    try {
        $result = python -c @"
import sys
sys.path.insert(0, r'$lerBase')
from agent.knowledge_consolidator import register_learning
register_learning(r'$FilePath')
print('OK')
"@ 2>&1
        Write-Log "Consolidator: $result"
    } catch {
        Write-Log "ERRO: $_"
    }
}

function Invoke-GitSync {
    param([string]$RepoPath, [string]$Label, [string]$SyncFile)
    $now = Get-Date
    $lastSync = if (Test-Path $SyncFile) { Get-Content $SyncFile -Raw -ErrorAction SilentlyContinue | ForEach-Object { try { [datetime]$_ } catch { [datetime]::MinValue } } } else { [datetime]::MinValue }
    if ($lastSync -eq $null) { $lastSync = [datetime]::MinValue }
    $elapsed = [math]::Round(($now - $lastSync).TotalSeconds)
    if ($elapsed -lt $gitInterval) { return }

    try {
        Push-Location $RepoPath -ErrorAction Stop
        $gitStatus = git status --porcelain 2>&1 | Out-String
        if ($gitStatus.Trim()) {
            git add -A 2>&1 | Out-Null
            $dateStr = Get-Date -Format "yyyy-MM-dd HH:mm"
            $msg = "[auto] $Label - $dateStr"
            git commit -m $msg 2>&1 | Out-Null
            git push 2>&1 | Out-Null
            Write-Log "Git sync ($Label): commit + push OK"
        }
        Pop-Location
        (Get-Date).ToString("o") | Out-File $SyncFile -Encoding UTF8 -Force
    } catch {
        Write-Log "Git sync ($Label) ignorado: $_"
    }
}

Write-Log "Vigilante pronto (polling a cada ${pollInterval}s)."

# ─── Keep alive: polling loop ─────────────────────────────────────────
while ($true) {
    try {
        Start-Sleep -Seconds $pollInterval

        # Poll for new/modified files
        if (Test-Path $learnDir) {
            $files = Get-ChildItem $learnDir -Filter "*.md" -ErrorAction Stop
            foreach ($f in $files) {
                try {
                    $hash = Get-FileHash $f.FullName -Algorithm MD5 -ErrorAction Stop
                    $key = $f.FullName.ToLower()
                    $lastHash = $knownHashes[$key]

                    if ($lastHash -ne $hash.Hash) {
                        $knownHashes[$key] = $hash.Hash
                        Start-Sleep -Seconds $debounceSeconds
                        if (Test-Path $f.FullName) {
                            Invoke-Register $f.FullName
                        }
                    }
                } catch {
                    Write-Log "Erro processando $($f.Name): $_"
                }
            }
        }

        Invoke-GitSync -RepoPath $ecoDir -Label "EcoSystemUmGrau" -SyncFile $ecoGitSyncFile
        Invoke-GitSync -RepoPath $lerDir -Label "LER" -SyncFile $lerGitSyncFile
    } catch {
        Write-Log "Erro no loop principal: $_"
        Write-Log "Detalhes: $($_.ScriptStackTrace)"
    }
}
