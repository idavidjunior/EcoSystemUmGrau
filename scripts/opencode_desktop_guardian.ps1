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
$script:log = [System.IO.StreamWriter]::new($LogPath, $true)
$script:log.AutoFlush = $true
function Write-Log { param($Msg) $script:log.WriteLine("[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Msg") }

function Rotate-Log {
    param([string]$Path, [int]$MaxBytes = 2MB)
    try {
        $fi = [System.IO.FileInfo]::new($Path)
        if ($fi.Exists -and $fi.Length -gt $MaxBytes) {
            $script:log.Close()
            $lines = [System.IO.File]::ReadAllLines($Path)
            $half = [math]::Floor($lines.Length / 2)
            $tail = $lines[$half..($lines.Length-1)]
            [System.IO.File]::WriteAllLines($Path, $tail)
            $script:log = [System.IO.StreamWriter]::new($Path, $true)
            $script:log.AutoFlush = $true
            $script:log.WriteLine("[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Log rotacionado: $($lines.Length) → $($tail.Length) linhas")
        }
    } catch {}
}

$EXE = "C:\Users\David Jr\AppData\Local\Programs\@opencode-aidesktop\OpenCode.exe"
$GPU_FLAGS = "--disable-gpu --disable-gpu-compositing --in-process-gpu --no-sandbox"
$LOG_ROOT = "C:\Users\David Jr\AppData\Roaming\ai.opencode.desktop\logs"
$SHORTCUTS = @(
    "C:\Users\David Jr\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\OpenCode.lnk",
    "C:\Users\David Jr\Desktop\OpenCode.lnk"
)

function Get-FreeRamMB { [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024, 0) }

function Test-DesktopRunning {
    # IMPORTANTE: Get-Process -Name OpenCode e CASE-INSENSITIVE e tambem pega o opencode.exe (CLI).
    # Usar Win32_Process e comparar o nome EXATO (case-sensitive via -ceq) para distinguir.
    $procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -ceq "OpenCode.exe" }
    if (-not $procs) { return $false }
    # Considera "rodando" se algum processo OpenCode.exe tem MainWindowHandle != 0
    foreach ($pp in $procs) {
        try {
            $gp = Get-Process -Id $pp.ProcessId -ErrorAction Stop
            if ($gp.MainWindowHandle -ne [IntPtr]::Zero) { return $true }
        } catch {}
    }
    # Se nenhum tem janela mas existem 3+ processos (main + filhos), considera em carga
    return ($procs.Count -ge 3)
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
    # Conservador: so considera travado se (renderer.log parado ha muito tempo) E (janela nao responde).
    # So olha o renderer.log da SESSAO atual (mesmo diretorio da ultima sessao).
    $dir = Get-LatestLogDir
    if (-not $dir) { return $false }
    $r = Join-Path $dir.FullName "renderer.log"
    if (-not (Test-Path $r)) { return $false }
    $age = ((Get-Date) - (Get-Item $r).LastWriteTime).TotalSeconds
    if ($age -le $RendererMaxStallSec) { return $false }
    # renderer.log parado ha muito tempo -> checa se a janela esta realmente presa
    $main = Get-CimInstance Win32_Process | Where-Object { $_.Name -ceq "OpenCode.exe" } | ForEach-Object {
        try { Get-Process -Id $_.ProcessId -EA Stop } catch {} } | Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero } | Select-Object -First 1
    if (-not $main) { return $true } # janela sumiu mas processo vivo = preso
    return (-not $main.Responding)
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
    # Fecha processos concorrentes nao essenciais e notifica.
    # CUIDADO: nao matar o opencode.exe CLI que eh host de agentes/loops.
    # So mata opencode.exe que sejam orfaos "run" (nao serve, nao host interativo).
    $orphans = Get-CimInstance Win32_Process -Filter "Name='opencode.exe'" -EA SilentlyContinue | Where-Object {
        $cmd = $_.CommandLine
        # orfao = CLI interativo em pasta aleatoria, nao "serve"
        ($cmd -match "opencode\.exe run") -or
        ($cmd -match "opencode\.exe`" `"." -and $cmd -notmatch " serve")
    }
    if ($orphans) {
        $mem = 0; foreach ($o in $orphans) { try { $mem += [math]::Round((Get-Process -Id $o.ProcessId -EA Stop).WorkingSet64/1MB) } catch {} }
        foreach ($o in $orphans) { try { Stop-Process -Id $o.ProcessId -Force -EA Stop } catch {} }
        Write-Log "Memoria: limpou $($orphans.Count) opencode orfao (${mem}MB)"
    } else {
        Write-Log "Memoria: nenhum orfao opencode para limpar"
    }
}

Write-Log "Guardiao OpenCode Desktop iniciado (intervalo ${Interval}s, RAM critica ${RamCriticalMB}MB)"

$cycleCount = 0

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
            $desktopProcs = Get-CimInstance Win32_Process | Where-Object { $_.Name -ceq "OpenCode.exe" }
            foreach ($pr in $desktopProcs) { try { Stop-Process -Id $pr.ProcessId -Force -EA Stop } catch {} }
            Start-Sleep -Seconds 3
            Start-DesktopWithFlags
            Start-Sleep -Seconds 25
        } elseif (Test-RendererStalled) {
            Write-Log "Renderer parado ha >${RendererMaxStallSec}s - reiniciando desktop (prevencao)"
            $desktopProcs = Get-CimInstance Win32_Process | Where-Object { $_.Name -ceq "OpenCode.exe" }
            foreach ($pr in $desktopProcs) { try { Stop-Process -Id $pr.ProcessId -Force -EA Stop } catch {} }
            Start-Sleep -Seconds 3
            Start-DesktopWithFlags
            Start-Sleep -Seconds 25
        }
    }

    Start-Sleep -Seconds $Interval
    $cycleCount++
    if ($cycleCount % 1000 -eq 0) { Rotate-Log -Path $LogPath }
}

$script:log.Close()
