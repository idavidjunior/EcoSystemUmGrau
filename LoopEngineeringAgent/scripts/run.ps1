param(
    [string]$Goal = "",
    [switch]$Resume,
    [switch]$Status,
    [switch]$Reset,
    [switch]$Help
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

if ($Help) {
    @"
LOOP ENGINEERING AGENT v1.0

USAGE:
  .\run.ps1 -Goal "your goal here"
  .\run.ps1 -Resume          (resume from last checkpoint)
  .\run.ps1 -Status          (show current state)
  .\run.ps1 -Reset           (reset all state)
  .\run.ps1 -Help            (this help)

EXAMPLES:
  .\run.ps1 -Goal "Create a Python script that prints hello"
  .\run.ps1 -Resume
  .\run.ps1 -Status
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

if ($Status) {
    & $PythonCmd "$RootDir\loop.py" --status
    exit
}

if ($Reset) {
    & $PythonCmd "$RootDir\loop.py" --reset
    exit
}

if ($Resume) {
    & $PythonCmd "$RootDir\loop.py" --resume
    exit
}

if ($Goal) {
    & $PythonCmd "$RootDir\loop.py" $Goal
    exit
}

# Interactive mode
Write-Host ""
Write-Host "LOOP ENGINEERING AGENT v1.0" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan
$Goal = Read-Host "Enter your goal"
if ($Goal) {
    & $PythonCmd "$RootDir\loop.py" $Goal
} else {
    Write-Host "No goal provided." -ForegroundColor Yellow
}
