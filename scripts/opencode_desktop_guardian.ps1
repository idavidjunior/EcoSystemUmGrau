param(
    [int]$Interval = 30,
    [int]$RamCriticalMB = 700,
    [int]$RendererMaxStallSec = 120,
    [string]$LogPath = "$PSScriptRoot\opencode_desktop_guardian_log.txt"
)

# Guardiao preventivo do OpenCode Desktop.
# Monitora: (1) processo desktop vivo, (2) renderer ativo, (3) memoria critica.
# Age ANTES que o app feche por pressao, e renicia com flags de GPU desabilitadas se cair.

$ErrorActionPreference = "SilentlyContinue"
$log = [System.IO.StreamWriter]::new($LogPath, $true)
$log.AutoFlush = $true
function Write-Log { param($Msg) $log.WriteLine("[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Msg") }

$EXE = "C:\Users\David Jr\AppData\Local\Programs\@opencode-aidesktop\OpenCode.exe"
$GPU_FLAGS = "--disable-gpu --disable-gpu-compositing --in-process-gpu --no-sandbox"
$LOG_ROOT = "C:\Users\David Jr\AppData\Roaming\ai.opencode.desktop\logs"
$SHORTCUTS = @(
    "C:\Users\David Jr\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\OpenCode.lnk",
    "C:\Users\David Jr\Desktop\OpenCode.lnk"
)

function Get-FreeRamMB { [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024, 0) }

function Test-DesktopRunning {
    $p = Get-Process -Name OpenCode -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 }
    return [bool]$p
}

function Get-LatestLogDir {
    Get-ChildItem $LOG_ROOT -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
}

function Test-RendererCrashed {
    $dir = Get-LatestLogDir
    if (-not $dir) { return $false }
    $winLog = Join-Path $dir.FullName "window.log"
    $utilLog = Join-Path $dir.FullName "utility.log"
    $winCrash = (Test-Path $winLog) -and ((Get-Content $winLog -Raw) -match "reason: 'crashed'")
    $gpuCrash = (Test-Path $utilLog) -and ((Get-Content $utilLog -Raw) -match "type: 'GPU'")
    return ($winCrash -or $gpuCrash)
}

function Test-RendererStalled {
    # renderer.log parou de crescer por RendererMaxStallSec
    $dir = Get-LatestLogDir
    if (-not $dir) { return $false }
    $r = Join-Path $dir.FullName "renderer.log"
    if (-not (Test-Path $r)) { return $false }
    $age = ((Get-Date) - (Get-Item $r).LastWriteTime).TotalSeconds
    return ($age -gt $RendererMaxStallSec)
}

function Ensure-ShortcutFlags {
    # Revalida que os atalhos continuam com as flags apos update do app
    try {
        $sh = New-Object -ComObject WScript.Shell
        foreach ($lnk in $SHORTCUTS) {
            if (Test-Path $lnk) {
                $s = $sh.CreateShortcut($lnk)
                if ($s.Arguments -ne $GPU_FLAGS) {
                    $s.Arguments = $GPU_FLAGS; $s.Save()
                    Write-Log "Atalho re-corrigido: $lnk"
                }
            }
        }
    } catch { Write-Log "WARN ensure-flags: $($_.Exception.Message)" }
}

function Start-DesktopWithFlags {
    if (-not (Test-Path $EXE)) { Write-Log "ERRO: exe nao encontrado: $EXE"; return }
    Start-Process -FilePath $EXE -ArgumentList $GPU_FLAGS
    Write-Log "Desktop iniciado com flags GPU desabilitadas"
}

function Relieve-Memory {
    # Fecha processos concorrentes nao essenciais e notifica
    $orphanOc = Get-Process -Name opencode -ErrorAction SilentlyContinue | Where-Object {
        $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine
        $cmd -match "opencode\.exe run" -or ($cmd -match "opencode\.exe" -and $cmd -notmatch " serve" -and $cmd -notmatch "bin\\opencode\.exe")
    }
    if ($orphanOc) {
        $mem = 0; $orphanOc | ForEach-Object { $mem += [math]::Round($_.WorkingSet64/1MB) }
        $orphanOc | Stop-Process -Force
        Write-Log "Memoria: limpou $($orphanOc.Count) opencode orfao (${mem}MB)"
    }
}

Write-Log "Guardiao OpenCode Desktop iniciado (intervalo ${Interval}s, RAM critica ${RamCriticalMB}MB)"

# No boot: revalida atalhos e, se desktop nao estiver rodando, sobe com flags
Ensure-ShortcutFlags
if (-not (Test-DesktopRunning)) { Write-Log "Desktop ausente no start do guardiao - subindo"; Start-DesktopWithFlags; Start-Sleep -Seconds 25 }

while ($true) {
    $free = Get-FreeRamMB

    # (A) Preventivo: memoria critica ANTES de acumular pressao
    if ($free -lt $RamCriticalMB) {
        Write-Log "ALERTA preventivo: RAM livre ${free}MB < ${RamCriticalMB}MB - liberando concorrentes"
        Relieve-Memory
        Start-Sleep -Seconds 3
        $free = Get-FreeRamMB
        Write-Log "Apos alivio: RAM livre ${free}MB"
    }

    # (B) Desktop caiu
    if (-not (Test-DesktopRunning)) {
        Write-Log "Desktop ausente - reiniciando com flags GPU"
        Ensure-ShortcutFlags
        Start-DesktopWithFlags
        Start-Sleep -Seconds 25
        if (Test-DesktopRunning) { Write-Log "Desktop restaurado" } else { Write-Log "FALHA ao restaurar desktop" }
    } else {
        # (C) Desktop vivo mas renderer crashou ou travou
        if (Test-RendererCrashed) {
            Write-Log "Renderer/GPU crashou em runtime - reiniciando desktop"
            Get-Process -Name OpenCode -ErrorAction SilentlyContinue | Stop-Process -Force
            Start-Sleep -Seconds 3
            Start-DesktopWithFlags
            Start-Sleep -Seconds 25
        } elseif (Test-RendererStalled) {
            Write-Log "Renderer parado ha >${RendererMaxStallSec}s - reiniciando desktop (prevencao)"
            Get-Process -Name OpenCode -ErrorAction SilentlyContinue | Stop-Process -Force
            Start-Sleep -Seconds 3
            Start-DesktopWithFlags
            Start-Sleep -Seconds 25
        }
    }

    Start-Sleep -Seconds $Interval
}

$log.Close()
