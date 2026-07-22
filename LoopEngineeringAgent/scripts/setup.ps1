param(
    [switch]$Git
)

Write-Host "LOOP ENGINEERING AGENT v1.0 - Setup" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Write-Host "Root: $RootDir"

# Check Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "Python: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Python not found. Install Python 3.8+" -ForegroundColor Yellow
}

# Check Git
try {
    $gitVersion = git --version 2>&1
    Write-Host "Git: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Git not found." -ForegroundColor Yellow
}

# Init memory directories and files
$memDir = "$RootDir\memory"
$null = New-Item -ItemType Directory -Path $memDir -Force
$logsDir = "$RootDir\logs"
$null = New-Item -ItemType Directory -Path $logsDir -Force
$cpDir = "$RootDir\checkpoints"
$null = New-Item -ItemType Directory -Path $cpDir -Force

# Create memory files
$memFiles = @{
    "goal.md"     = "# Goal`n`nNo goal set yet.`n"
    "plan.md"     = "# Plan`n`nNo plan created yet.`n"
    "progress.json" = '{"steps": [], "current_step": 0, "completed_steps": [], "failed_steps": []}'
    "context.json" = "{}"
    "decisions.md" = "# Decisions Log`n`n"
    "errors.log"   = "# Errors Log`n`n"
}

foreach ($f in $memFiles.Keys) {
    $path = "$memDir\$f"
    if (-not (Test-Path $path)) {
        Set-Content -Path $path -Value $memFiles[$f] -Encoding UTF8
        Write-Host "  Created: memory/$f" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To run:" -ForegroundColor Cyan
Write-Host "  .\scripts\run.ps1 -Goal ""your goal here""" -ForegroundColor White
Write-Host ""

# Git setup
if ($Git) {
    & "$PSScriptRoot\git_setup.ps1"
}
