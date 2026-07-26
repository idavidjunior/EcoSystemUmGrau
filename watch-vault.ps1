<#
.SYNOPSIS
    Watcher automatico do vault Obsidian. Monitora Desktop\Codigos, sincroniza com GitHub,
    e NOTIFICA o usuario com som + popup detalhado.

.DESCRIPTION
    Roda em background. Detecta mudancas no vault, espera 10s de inatividade,
    executa sync-vault.ps1, git commit, git push.
    Para cada sync, emite som ascendente e popup com:
      - O que foi atualizado (lista de arquivos)
      - De onde (Desktop\Codigos)
      - Para onde (repo/vault/ -> GitHub)

    INSTALACAO como servico automatico:
      .\install-watcher.ps1

.PARAMETER VaultPath
    Onde monitorar (default: ~/Desktop/Codigos)
.PARAMETER RepoRoot
    Onde esta o repositorio (default: detecta自动)
.PARAMETER DebounceSeconds
    Segundos de inatividade antes de sincronizar (default: 10)
#>

param(
    [string]$VaultPath = "$env:USERPROFILE\Desktop\Codigos",
    [string]$RepoRoot = "",
    [int]$DebounceSeconds = 10,
    [switch]$TestMode = $false
)

# Auto-detect repo root
if (-not $RepoRoot) {
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    # Walk up to find .git
    $checkDir = $scriptPath
    while ($checkDir -and -not (Test-Path "$checkDir\.git")) {
        $checkDir = Split-Path -Parent $checkDir
    }
    $RepoRoot = $checkDir
}

if (-not $RepoRoot -or -not (Test-Path "$RepoRoot\.git")) {
    Write-Error "[FATAL] Repositorio nao encontrado a partir de $scriptPath"
    exit 1
}

$SyncScript = "$RepoRoot\sync-vault.ps1"
$VaultInRepo = "$RepoRoot\vault"

# ============================================================
# POPUP DE NOTIFICACAO
# ============================================================
function Show-SyncNotification {
    param(
        [string[]]$ChangedFiles,
        [string]$Status,  # "ok" | "error"
        [string]$ErrorMessage = ""
    )

    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    $form = New-Object System.Windows.Forms.Form
    $form.Text = "Vault Sync - Obsidian para GitHub"
    $form.Size = New-Object System.Drawing.Size(520, 380)
    $form.StartPosition = "CenterScreen"
    $form.TopMost = $true
    $form.ControlBox = $true
    $form.ShowInTaskbar = $true
    $form.Icon = [System.Drawing.Icon]::ExtractAssociatedIcon("powershell.exe")

    # Cor de fundo
    $form.BackColor = [System.Drawing.Color]::FromArgb(240, 240, 245)

    # Titulo
    $title = New-Object System.Windows.Forms.Label
    $title.Text = if ($Status -eq "ok") {
        "✅ VAULT SINCRONIZADO COM GITHUB"
    } else {
        "❌ ERRO NA SINCRONIZACAO"
    }
    $title.Font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
    $title.ForeColor = if ($Status -eq "ok") { [System.Drawing.Color]::DarkGreen } else { [System.Drawing.Color]::DarkRed }
    $title.Size = New-Object System.Drawing.Size(480, 30)
    $title.Location = New-Object System.Drawing.Point(20, 15)
    $form.Controls.Add($title)

    # Timestamp
    $ts = New-Object System.Windows.Forms.Label
    $ts.Text = (Get-Date -Format "dd/MM/yyyy HH:mm:ss")
    $ts.Font = New-Object System.Drawing.Font("Segoe UI", 9)
    $ts.ForeColor = [System.Drawing.Color]::Gray
    $ts.Size = New-Object System.Drawing.Size(480, 20)
    $ts.Location = New-Object System.Drawing.Point(20, 48)
    $form.Controls.Add($ts)

    # Origem
    $srcLabel = New-Object System.Windows.Forms.Label
    $srcLabel.Text = "DE: $VaultPath"
    $srcLabel.Font = New-Object System.Drawing.Font("Segoe UI", 8)
    $srcLabel.ForeColor = [System.Drawing.Color]::DimGray
    $srcLabel.Size = New-Object System.Drawing.Size(480, 18)
    $srcLabel.Location = New-Object System.Drawing.Point(20, 72)
    $form.Controls.Add($srcLabel)

    # Destino
    $dstLabel = New-Object System.Windows.Forms.Label
    $dstLabel.Text = "PARA: $VaultInRepo -> GitHub (opencode/mighty-meadow)"
    $dstLabel.Font = New-Object System.Drawing.Font("Segoe UI", 8)
    $dstLabel.ForeColor = [System.Drawing.Color]::DimGray
    $dstLabel.Size = New-Object System.Drawing.Size(480, 18)
    $dstLabel.Location = New-Object System.Drawing.Point(20, 92)
    $form.Controls.Add($dstLabel)

    if ($Status -eq "error") {
        $errBox = New-Object System.Windows.Forms.TextBox
        $errBox.Text = $ErrorMessage
        $errBox.Multiline = $true
        $errBox.ReadOnly = $true
        $errBox.ScrollBars = "Vertical"
        $errBox.Size = New-Object System.Drawing.Size(480, 150)
        $errBox.Location = New-Object System.Drawing.Point(20, 120)
        $errBox.BackColor = [System.Drawing.Color]::FromArgb(255, 240, 240)
        $form.Controls.Add($errBox)
    } else {
        # Lista de arquivos alterados
        $listLabel = New-Object System.Windows.Forms.Label
        $listLabel.Text = "ARQUIVOS ATUALIZADOS ($($ChangedFiles.Count)):"
        $listLabel.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
        $listLabel.Size = New-Object System.Drawing.Size(480, 20)
        $listLabel.Location = New-Object System.Drawing.Point(20, 120)
        $form.Controls.Add($listLabel)

        $listBox = New-Object System.Windows.Forms.ListBox
        $listBox.Size = New-Object System.Drawing.Size(480, 150)
        $listBox.Location = New-Object System.Drawing.Point(20, 145)
        $listBox.Font = New-Object System.Drawing.Font("Consolas", 8)
        $listBox.ScrollAlwaysVisible = $true

        # Max 50 items for display
        $displayFiles = $ChangedFiles | Select-Object -First 50
        if ($ChangedFiles.Count -gt 50) {
            $displayFiles += "... e mais $($ChangedFiles.Count - 50) arquivos"
        }
        $displayFiles | ForEach-Object { [void]$listBox.Items.Add($_) }
        $form.Controls.Add($listBox)
    }

    # Botao Fechar
    $btn = New-Object System.Windows.Forms.Button
    $btn.Text = "FECHAR"
    $btn.Size = New-Object System.Drawing.Size(100, 30)
    $btn.Location = New-Object System.Drawing.Point(400, $form.Height - 65)
    $btn.BackColor = [System.Drawing.Color]::FromArgb(50, 50, 55)
    $btn.ForeColor = [System.Drawing.Color]::White
    $btn.FlatStyle = "Flat"
    $btn.Add_Click({ $form.Close() })
    $form.Controls.Add($btn)

    # Auto-fechar em 30s
    $timer = New-Object System.Windows.Forms.Timer
    $timer.Interval = 30000
    $timer.Add_Tick({ $form.Close() })
    $timer.Start()

    # Mostrar (nao bloqueante)
    $form.ShowDialog() | Out-Null
}

# ============================================================
# SOM DE NOTIFICACAO
# ============================================================
function Play-SyncSound {
    param([string]$Type = "success")  # "success" | "error"

    if ($Type -eq "success") {
        # 3 beeps ascendentes: som caracteristico de sync completo
        [System.Console]::Beep(660, 150)
        Start-Sleep -Milliseconds 80
        [System.Console]::Beep(880, 150)
        Start-Sleep -Milliseconds 80
        [System.Console]::Beep(1100, 250)
    } else {
        # 2 beeps graves descendentes: erro
        [System.Console]::Beep(400, 200)
        Start-Sleep -Milliseconds 100
        [System.Console]::Beep(300, 300)
    }
}

# ============================================================
# DETECTAR MUDANCAS (diff entre vault e repo)
# ============================================================
function Get-ChangedFiles {
    param([string[]]$Events)

    $changed = @()
    foreach ($e in $Events) {
        # Parse "Created: path\file.txt" or "Changed: path\file.txt"
        if ($e -match "^[^:]+:\s+(.+)$") {
            $path = $Matches[1].Trim()
            # Normalize to relative path
            if ($path.StartsWith($VaultPath)) {
                $relPath = $path.Substring($VaultPath.Length).TrimStart('\')
                if ($relPath) { $changed += $relPath }
            }
        }
    }
    return $changed | Sort-Object -Unique
}

# ============================================================
# WATCHER PRINCIPAL
# ============================================================
function Start-VaultWatcher {
    Write-Host @"

============================================
  WATCHER DO VAULT - Auto Sync para GitHub
============================================
  Monitorando: $VaultPath
  Repositorio: $RepoRoot
  Sincroniza a cada: $DebounceSeconds seg de inatividade
  Notificacao: Popup + Som
============================================
"@ -ForegroundColor Cyan

    if (-not (Test-Path $VaultPath)) {
        Write-Error "[ERRO] Vault nao encontrado: $VaultPath"
        exit 1
    }

    # Criar FileSystemWatcher
    $watcher = New-Object System.IO.FileSystemWatcher
    $watcher.Path = $VaultPath
    $watcher.IncludeSubdirectories = $true
    $watcher.NotifyFilter = [System.IO.NotifyFilters]::FileName -bor
                            [System.IO.NotifyFilters]::DirectoryName -bor
                            [System.IO.NotifyFilters]::LastWrite

    # Excluir diretorios de build do monitoramento
    $excludeDirs = @(
        "\.git", "\.cxx\", "\.gradle\", "\.gradle_temp\", "build_output\",
        "Reprodutor MP3 player\", "bin\", "obj\", "__pycache__\", ".pytest_cache\", "node_modules\",
        "\.obsidian\"
    )

    $eventQueue = [System.Collections.ArrayList]::new()
    $syncTimer = $null
    $lock = [System.Threading.Mutex]::new()
    $lastEventTime = Get-Date
    $isSyncing = $false

    # Handler: coleta eventos
    $onEvent = {
        param($source, $e)
        $lock.WaitOne()
        try {
            $fullPath = $e.FullPath
            # Verificar exclusoes
            $excluded = $false
            foreach ($ex in $excludeDirs) {
                if ($fullPath -match [regex]::Escape($ex)) { $excluded = $true; break }
            }
            if (-not $excluded -and (Test-Path $fullPath -ErrorAction SilentlyContinue)) {
                $eventQueue.Add("$($e.ChangeType): $fullPath") | Out-Null
                $global:lastEventTime = Get-Date
            }
        } finally { $lock.ReleaseMutex() }
    }

    # Registrar eventos
    $handlers = @()
    $handlers += Register-ObjectEvent -InputObject $watcher -EventName Created -Action $onEvent
    $handlers += Register-ObjectEvent -InputObject $watcher -EventName Changed -Action $onEvent
    $handlers += Register-ObjectEvent -InputObject $watcher -EventName Deleted -Action $onEvent
    $handlers += Register-ObjectEvent -InputObject $watcher -EventName Renamed -Action $onEvent

    $watcher.EnableRaisingEvents = $true

    Write-Host "[WATCHER] Ativo. Aguardando alteracoes no vault..." -ForegroundColor Green

    # Se for modo teste, simular um evento
    if ($TestMode) {
        Write-Host "[TESTE] Modo teste ativado. Simulando sync..." -ForegroundColor Yellow
        $eventQueue.Add("Test: modo de teste") | Out-Null
        Start-Sleep 2
        Invoke-Sync
        $watcher.EnableRaisingEvents = $false
        foreach ($h in $handlers) { Unregister-Event -SourceIdentifier $h.Name -ErrorAction SilentlyContinue }
        return
    }

    # Loop principal: verifica se precisa sincronizar
    try {
        while ($true) {
            $lock.WaitOne()
            $queueCount = $eventQueue.Count
            $idle = (Get-Date) - $lastEventTime
            $lock.ReleaseMutex()

            if ($queueCount -gt 0 -and $idle.TotalSeconds -ge $DebounceSeconds -and -not $isSyncing) {
                Invoke-Sync
            }
            Start-Sleep -Milliseconds 500
        }
    } finally {
        $watcher.EnableRaisingEvents = $false
        foreach ($h in $handlers) { Unregister-Event -SourceIdentifier $h.Name -ErrorAction SilentlyContinue }
    }
}

# ============================================================
# EXECUTAR SINCRONIZACAO
# ============================================================
function Invoke-Sync {
    $lock.WaitOne()
    $isSyncing = $true
    $events = $eventQueue.ToArray()
    $eventQueue.Clear()
    $lock.ReleaseMutex()

    Write-Host "" 
    Write-Host "[SYNC] Iniciando sincronizacao..." -ForegroundColor Cyan

    # 1. Extrair arquivos alterados
    $changedFiles = Get-ChangedFiles -Events $events
    if ($changedFiles.Count -eq 0) { $changedFiles = @("<alteracoes detectadas>") }

    # 2. Rodar sync-vault.ps1
    $syncOk = $true
    $errorMsg = ""
    if (Test-Path $SyncScript) {
        Write-Host "[SYNC] Executando sync-vault.ps1..." -ForegroundColor Cyan
        $syncResult = & $SyncScript 2>&1
        if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
            $syncOk = $false
            $errorMsg = "sync-vault.ps1 falhou (exit code: $LASTEXITCODE)"
            Write-Host "[ERRO] $errorMsg" -ForegroundColor Red
        }
    }

    # 3. Git add + commit + push
    if ($syncOk) {
        Push-Location $RepoRoot
        try {
            git add "vault/" 2>$null

            $hasChanges = git status --short "vault/" 2>$null
            if ($hasChanges) {
                $msg = "auto-sync vault: $($changedFiles.Count) arquivo(s) alterado(s)"
                git commit -m "$msg" 2>&1 | Out-Null
                Write-Host "[SYNC] Commit realizado: $msg" -ForegroundColor Green

                # Push (tenta, mas nao falha se offline)
                $pushResult = git push origin HEAD 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "[SYNC] Push enviado para GitHub" -ForegroundColor Green
                } else {
                    Write-Host "[AVISO] Push falhou (provavelmente offline). Commit salvo localmente." -ForegroundColor Yellow
                }
            } else {
                Write-Host "[SYNC] Nenhuma alteracao nova para commitar" -ForegroundColor Yellow
                $changedFiles = @("<metadados do vault alterados>")
            }
        } catch {
            $syncOk = $false
            $errorMsg = "Git error: $_"
            Write-Host "[ERRO] $errorMsg" -ForegroundColor Red
        } finally {
            Pop-Location
        }
    }

    # 4. NOTIFICAR USUARIO
    if ($syncOk) {
        Play-SyncSound -Type "success"
        Write-Host "[NOTIFICACAO] Sync concluido. Exibindo popup..." -ForegroundColor Cyan
    } else {
        Play-SyncSound -Type "error"
        Write-Host "[NOTIFICACAO] Sync falhou. Exibindo popup de erro..." -ForegroundColor Red
    }

    # Mostrar popup (em segundo plano para nao travar o watcher)
    $notifParams = @{
        ChangedFiles  = $changedFiles
        Status        = if ($syncOk) { "ok" } else { "error" }
        ErrorMessage  = $errorMsg
    }
    # Iniciar em job separado para nao bloquear
    Start-Job -ScriptBlock {
        param($p) Show-SyncNotification @p
        Play-SyncSound -Type $p.Status
    } -ArgumentList $notifParams | Out-Null

    $isSyncing = $false
    Write-Host "[SYNC] Watcher retomando monitoramento..." -ForegroundColor Cyan
}

# ============================================================
# INICIALIZACAO
# ============================================================

# Garantir que o sync script existe
if (-not (Test-Path $SyncScript)) {
    Write-Warning "[AVISO] sync-vault.ps1 nao encontrado em $SyncScript"
    Write-Warning "[AVISO] A sincronizacao via sync-vault.ps1 sera pulada"
}

Start-VaultWatcher
