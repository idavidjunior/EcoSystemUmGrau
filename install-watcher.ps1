<#
.SYNOPSIS
    Instala o watch-vault.ps1 como servico Windows (Scheduled Task)
    que roda em background e inicia automaticamente ao fazer login.

.DESCRIPTION
    Cria uma tarefa agendada que:
      - Inicia quando o usuario faz login
      - Roda o watcher invisivel (janela oculta)
      - Monitora Desktop\Codigos e sincroniza com GitHub
      - Mostra popup + som a cada sync

    Tambem cria um atalho desinstalar facil.

    USO:
        .\install-watcher.ps1              # Instalar
        .\install-watcher.ps1 -Uninstall   # Desinstalar
        .\install-watcher.ps1 -Status      # Ver status
#>

param(
    [switch]$Uninstall,
    [switch]$Status
)

$taskName = "VaultAutoSyncWatcher"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$watcherScript = "$repoRoot\watch-vault.ps1"
$uninstallScript = "$repoRoot\uninstall-watcher.ps1"

if ($Uninstall) {
    Write-Host "[UNINSTALL] Removendo tarefa '$taskName'..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

    # Mata processos watch-vault ativos
    Get-Process -Name "powershell" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -match "watch-vault"
    } | Stop-Process -Force -ErrorAction SilentlyContinue

    Write-Host "[UNINSTALL] Watcher removido." -ForegroundColor Green
    exit 0
}

if ($Status) {
    try {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
        Write-Host @"
STATUS DO WATCHER:
  Nome:     $taskName
  Estado:   $($task.State)
  Ultima execucao: $($task.LastRunTime)
  Proxima execucao: $($task.NextRunTime)

"@ -ForegroundColor Cyan

        # Verificar se tem processo rodando
        $procs = Get-Process -Name "powershell" -ErrorAction SilentlyContinue |
                 Where-Object { $_.CommandLine -match "watch-vault" }
        if ($procs) {
            Write-Host "Processo watch-vault ativo: PID $($procs.Id)" -ForegroundColor Green
        } else {
            Write-Host "Processo watch-vault: INATIVO" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Watcher NAO instalado." -ForegroundColor Red
    }
    exit 0
}

# Verificar prereqs
if (-not (Test-Path $watcherScript)) {
    Write-Error "[ERRO] watch-vault.ps1 nao encontrado em $watcherScript"
    exit 1
}

# Criar script de entrada que lanca o watcher sem janela
$launchScript = @"
`$repoRoot = "$repoRoot"
`$watcher = "$watcherScript"
`$logFile = "`$env:USERPROFILE\Desktop\watch-vault.log"

# Iniciar watcher em janela oculta (usar $proc, nao $ps - $ps e var automatica do PowerShell)
`$proc = Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`$watcher"
) -WindowStyle Hidden -PassThru

# Salvar PID para referencia
$pidValue = if (`$proc) { `$proc.Id } else { "desconhecido" }
"`$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [START] Watch-Vault iniciado (PID: $pidValue)" | Out-File -FilePath `$logFile -Append

# Aguardar
if (`$proc) { `$proc.WaitForExit() }

$exitCode = if (`$proc) { `$proc.ExitCode } else { "?" }
"`$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [EXIT] Watch-Vault encerrado (ExitCode: $exitCode)" | Out-File -FilePath `$logFile -Append
"@

$launcherPath = "$env:USERPROFILE\.vault-watch-launcher.ps1"
Set-Content -Path $launcherPath -Value $launchScript -Encoding UTF8

# Remover tarefa existente se houver
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Criar tarefa agendada que roda no login
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument @"
-NoProfile -ExecutionPolicy Bypass -File "$launcherPath"
"@

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Limited

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null

Write-Host @"

✅ WATCHER DO VAULT INSTALADO COM SUCESSO!
==========================================
  Nome da tarefa: $taskName
  Inicia automaticamente ao: LOGIN
  Monitora: $env:USERPROFILE\Desktop\Codigos
  Sincroniza para: $repoRoot\vault\ -> GitHub
  Notificacao: Popup + Som (3 beeps ascendentes)
==========================================

COMANDOS UTEIS:
  Ver status:    .\install-watcher.ps1 -Status
  Desinstalar:   .\install-watcher.ps1 -Uninstall
  Testar agora:  & '$watcherScript' -TestMode

OBS: O watcher comeca automaticamente na proxima vez que voce fizer login.
Para iniciar AGORA sem reiniciar:
  Start-ScheduledTask -TaskName '$taskName'

"@ -ForegroundColor Green

# Criar script de desinstalacao
@"
# Uninstall watcher
& "$psScriptRoot\install-watcher.ps1" -Uninstall
Remove-Item "$env:USERPROFILE\.vault-watch-launcher.ps1" -Force -ErrorAction SilentlyContinue
Write-Host "Watcher removido completamente." -ForegroundColor Green
Start-Sleep 2
"@ | Set-Content -Path $uninstallScript -Encoding UTF8

Write-Host "[DICA] Script de desinstalacao criado: $uninstallScript" -ForegroundColor Cyan
