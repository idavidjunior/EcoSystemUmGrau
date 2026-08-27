param(
    [int]$Interval = 20,
    [string]$LogPath = "$PSScriptRoot\watchdog_log.txt"
)

$ErrorActionPreference = "SilentlyContinue"

# =====================================================================
# WATCHDOG REBAIXADO A KEEPER (unificacao de vigilantes - 2026)
# ---------------------------------------------------------------------
# O watchdog.ps1 deixou de vigiar bridge/serve/orfaos/widget: essa e agora
# responsabilidade UNICA do scripts/system_guardian.py (Python). Aqui so
# garantimos que os dois orquestradores do ecossistema estejam vivos.
# Cadeia de supervisao: watchdog -> vigilante.ps1 -> system_guardian.py.
# Mantido o watchdog_start.bat (boot do Windows) e o log watchdog_log.txt
# intactos para nao quebrar outras integracoes. A protecao do desktop
# OpenCode continua a cargo do system_guardian.py (clausula petrea).
# =====================================================================

# Instancia unica via arquivo de lock com PID.
$LockPath = "$PSScriptRoot\watchdog.lock"
$meuPid = $PID
$jaExiste = $false
if (Test-Path $LockPath) {
    try {
        $outroPid = [int](Get-Content $LockPath -Raw).Trim()
        $procOutro = Get-Process -Id $outroPid -ErrorAction SilentlyContinue
        if ($procOutro -and $procOutro.ProcessName -match "powershell") {
            $jaExiste = $true
        }
    } catch { }
}
if ($jaExiste) { exit 0 }
try { Set-Content -Path $LockPath -Value $meuPid -Encoding ascii } catch { }

# Log com limite de tamanho (~2MB): ao estourar, descarta a metade mais antiga.
if (Test-Path $LogPath) {
    $info = Get-Item $LogPath
    if ($info.Length -gt 2MB) {
        $linhas = Get-Content $LogPath
        $linhas | Select-Object -Skip ([int]($linhas.Count / 2)) | Set-Content $LogPath
    }
}
$log = [System.IO.StreamWriter]::new($LogPath, $true)
$log.AutoFlush = $true
function Write-Log { param($Msg) $log.WriteLine("[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Msg") }

$PYTHON = "C:\Users\David Jr\AppData\Local\Programs\Python\Python312\python.exe"
$ScriptDir = $PSScriptRoot
$Vigilante = Join-Path $ScriptDir "vigilante.ps1"
$GuardianPy = Join-Path $ScriptDir "system_guardian.py"

function Ensure-Running {
    param(
        [string]$ProcessName,
        [string]$CmdPattern,
        [scriptblock]$StartAction
    )
    $found = $false
    try {
        $procs = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
        foreach ($pr in $procs) {
            $cim = Get-CimInstance Win32_Process -Filter "ProcessId=$($pr.Id)" -ErrorAction SilentlyContinue
            if ($cim -and $cim.CommandLine -like "*$CmdPattern*") { $found = $true; break }
        }
    } catch { }
    if (-not $found) {
        try { & $StartAction; Write-Log "$CmdPattern iniciado pelo watchdog" }
        catch { Write-Log "ERRO ao iniciar $CmdPattern : $($_.Exception.Message)" }
    }
}

function Start-Guardian {
    Start-Process -FilePath $PYTHON -ArgumentList "-u `"$GuardianPy`"" -WorkingDirectory $ScriptDir -WindowStyle Hidden
}
function Start-Vigilante {
    Start-Process -FilePath "powershell" -ArgumentList "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Vigilante`"" -WindowStyle Hidden
}

Write-Log "Watchdog rebaixado a keeper (boot do ecossistema). Intervalo: ${Interval}s"

while ($true) {
    Ensure-Running -ProcessName "powershell" -CmdPattern "vigilante.ps1" -StartAction ${function:Start-Vigilante}
    Ensure-Running -ProcessName "python" -CmdPattern "system_guardian" -StartAction ${function:Start-Guardian}
    Start-Sleep -Seconds $Interval
}

$log.Close()
try { Remove-Item -Path $LockPath -Force -ErrorAction SilentlyContinue } catch { }
