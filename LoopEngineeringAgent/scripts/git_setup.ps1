param(
    [string]$RepoUrl = ""
)

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

# Check if .gitignore exists
$gitignorePath = "$RootDir\.gitignore"
if (-not (Test-Path $gitignorePath)) {
    @"
# Loop Engineering Agent - .gitignore

# Environment
.env
config/.env

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/

# Checkpoints and logs
checkpoints/*
logs/*
!checkpoints/.gitkeep
!logs/.gitkeep

# Memory (keep structure, not content)
memory/*
!memory/.gitkeep

# Projects
projects/*
!projects/.gitkeep

# OS
Thumbs.db
.DS_Store

# IDE
.idea/
.vscode/
*.swp
*.swo
"@ | Set-Content -Path $gitignorePath -Encoding UTF8
    Write-Host "Created .gitignore" -ForegroundColor Green
}

# Initialize git repo
if (-not (Test-Path "$RootDir\.git")) {
    git init
    Write-Host "Git repo initialized" -ForegroundColor Green
}

# Create .gitkeep files
New-Item -ItemType File -Path "$RootDir\checkpoints\.gitkeep" -Force | Out-Null
New-Item -ItemType File -Path "$RootDir\logs\.gitkeep" -Force | Out-Null
New-Item -ItemType File -Path "$RootDir\memory\.gitkeep" -Force | Out-Null
New-Item -ItemType File -Path "$RootDir\projects\.gitkeep" -Force | Out-Null

# Git user config (from global)
$userName = git config --global user.name
$userEmail = git config --global user.email
if ($userName -and $userEmail) {
    git config user.name $userName
    git config user.email $userEmail
    Write-Host "Git user configured: $userName <$userEmail>" -ForegroundColor Green
}

if ($RepoUrl) {
    $remoteExists = git remote get-url origin 2>$null
    if (-not $remoteExists) {
        git remote add origin $RepoUrl
        Write-Host "Remote origin set: $RepoUrl" -ForegroundColor Green
    } else {
        Write-Host "Remote origin already exists: $remoteExists" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Git setup complete!" -ForegroundColor Green
Write-Host "Current status:" 
git status
