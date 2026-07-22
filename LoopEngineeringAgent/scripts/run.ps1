param(
    [string]$Goal = "",
    [switch]$Resume,
    [switch]$Status,
    [switch]$Reset,
    [switch]$Report,
    [switch]$Bridge,
    [switch]$Help
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

if ($Help) {
    @"
LOOP ENGINEERING AGENT v1.1

USAGE:
  .\run.ps1 -Goal "your goal here"     Start agent with a goal
  .\run.ps1 -Resume                     Resume from last checkpoint
  .\run.ps1 -Status                     Show current status
  .\run.ps1 -Reset                      Reset all state
  .\run.ps1 -Report                     Generate final report
  .\run.ps1 -Bridge "goal"              Run in OpenCode bridge mode
  .\run.ps1 -Help                       Show this help
"@
    exit
}

$PythonCmd = "python"
try {
    $null = Get-Command python -ErrorAction Stop
} catch {
    try {
        $null = Get-Command python3 -ErrorAction Stop
        $PythonCmd = "python3"
    } catch {
        Write-Host "ERROR: Python not found. Install Python 3.8+" -ForegroundColor Red
        exit 1
    }
}

if ($Status) { & $PythonCmd "$RootDir\loop.py" --status; exit }
if ($Reset)  { & $PythonCmd "$RootDir\loop.py" --reset; exit }
if ($Report) { & $PythonCmd "$RootDir\loop.py" --report; exit }
if ($Resume) { & $PythonCmd "$RootDir\loop.py" --resume; exit }
if ($Bridge) { & $PythonCmd "$RootDir\loop.py" --bridge $Goal; exit }
if ($Goal)   { & $PythonCmd "$RootDir\loop.py" $Goal; exit }

Write-Host ""
Write-Host "LOOP ENGINEERING AGENT v1.1" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan
$Goal = Read-Host "Enter your goal"
if ($Goal) {
    & $PythonCmd "$RootDir\loop.py" $Goal
} else {
    Write-Host "No goal provided." -ForegroundColor Yellow
}
