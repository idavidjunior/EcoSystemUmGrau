param([switch]$Git)

Write-Host "LOOP ENGINEERING AGENT v1.1 - Setup" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Write-Host "Root: $RootDir"

try { $pyVersion = python --version 2>&1; Write-Host "Python: $pyVersion" -ForegroundColor Green }
catch { Write-Host "WARNING: Python not found" -ForegroundColor Yellow }

try { $gitVersion = git --version 2>&1; Write-Host "Git: $gitVersion" -ForegroundColor Green }
catch { Write-Host "WARNING: Git not found" -ForegroundColor Yellow }

# Create directory structure
$dirs = @(
    "agent", "core", "memory", "config", "logs", "checkpoints", "projects",
    "scripts", "omni_route", "integrations", "integrations\opencode",
    "reports", "tests",
    "memory\projects", "memory\knowledge", "memory\user_preferences",
    "memory\technical_history", "memory\successful_architectures"
)
foreach ($d in $dirs) {
    $null = New-Item -ItemType Directory -Path "$RootDir\$d" -Force
}

# Create memory files
$memFiles = @{
    "goal.md"                = "# Goal`n`nNo goal set yet.`n"
    "plan.md"                = "# Plan`n`nNo plan created yet.`n"
    "progress.json"          = '{"steps": [], "current_step": 0, "completed_steps": [], "failed_steps": []}'
    "context.json"           = "{}"
    "decisions.md"           = "# Decisions Log`n`n"
    "errors.log"             = "# Errors Log`n`n"
    "learned_rules.json"     = '{"rules": []}'
    "successful_patterns.json" = '{"patterns": []}'
    "failed_patterns.json"   = '{"patterns": []}'
}
foreach ($f in $memFiles.Keys) {
    $path = "$RootDir\memory\$f"
    if (-not (Test-Path $path)) {
        Set-Content -Path $path -Value $memFiles[$f] -Encoding UTF8
        Write-Host "  Created: memory/$f" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To run:" -ForegroundColor Cyan
Write-Host "  .\scripts\run.ps1 -Goal ""your goal""" -ForegroundColor White
Write-Host ""

if ($Git) { & "$PSScriptRoot\git_setup.ps1" }
