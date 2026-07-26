<#
.SYNOPSIS
    Bootstrap do Ecossistema LER + OpenCode + Obsidian em maquina nova.
.DESCRIPTION
    Instala OpenCode, clona o repositorio, configura skills, vault, MCP,
    variaveis de ambiente e watcher. Um comando, zero config previa.
.PARAMETER VaultPath
    Caminho para o vault Obsidian (default: ~/Desktop/Codigos)
.PARAMETER InstallDir
    Onde clonar o repositorio (default: ~/.local/share/opencode/worktree/mighty-meadow)
.PARAMETER Branch
    Branch do repositorio (default: opencode/mighty-meadow)
.EXAMPLE
    powershell -c "iex (iwr -useb https://raw.githubusercontent.com/idavidjunior/EcoSystemUmGrau/opencode/mighty-meadow/bootstrap.ps1)"
#>

param(
    [string]$VaultPath = "$env:USERPROFILE\Desktop\Codigos",
    [string]$InstallDir = "$env:LOCALAPPDATA\opencode\worktree\mighty-meadow",
    [string]$Branch = "opencode/mighty-meadow"
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Bootstrap Ecossistema LER v2.0"
$RepoUrl = "https://github.com/idavidjunior/EcoSystemUmGrau.git"
$SetupUrl = "https://raw.githubusercontent.com/idavidjunior/EcoSystemUmGrau/$Branch/setup.ps1"

function Step($title) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host ">>> $title" -ForegroundColor White -BackgroundColor DarkBlue
    Write-Host "========================================" -ForegroundColor Cyan
}

function CheckSuccess($desc) {
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        Write-Host "[FALHA] $desc" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] $desc" -ForegroundColor Green
}

# ============================================================
# PASSO 1: Pre-requisitos
# ============================================================
Step "1/6 - Verificando pre-requisitos"

$prereqs = @(
    @{Name="Git"; Cmd="git --version"},
    @{Name="Node.js 18+"; Cmd="node --version"},
    @{Name="npm"; Cmd="npm --version"},
    @{Name="PowerShell 5.1+"; Cmd="powershell -Command `$PSVersionTable.PSVersion"}
)

$allOk = $true
foreach ($p in $prereqs) {
    try {
        $out = cmd /c "$($p.Cmd) 2>&1"
        Write-Host "  [OK] $($p.Name): $($out -join '')" -ForegroundColor Green
    } catch {
        Write-Host "  [FALTA] $($p.Name) - Instale antes de prosseguir" -ForegroundColor Red
        Write-Host "    Git: https://git-scm.com/downloads"
        Write-Host "    Node.js: https://nodejs.org/"
        $allOk = $false
    }
}
if (-not $allOk) { exit 1 }

# ============================================================
# PASSO 2: Instalar OpenCode
# ============================================================
Step "2/6 - Instalando OpenCode"

$oc = Get-Command "opencode" -ErrorAction SilentlyContinue
if ($oc) {
    Write-Host "OpenCode ja instalado em $($oc.Source)" -ForegroundColor Green
} else {
    Write-Host "Instalando opencode-ai via npm..." -ForegroundColor Cyan
    npm install -g opencode-ai
    CheckSuccess "OpenCode instalado"
}

# ============================================================
# PASSO 3: Configurar variaveis de ambiente
# ============================================================
Step "3/6 - Configurando variaveis de ambiente"

[Environment]::SetEnvironmentVariable("VAULT_PATH", $VaultPath, "User")
Write-Host "  [OK] VAULT_PATH = $VaultPath" -ForegroundColor Green

Write-Host "`nATENCAO: Configure suas chaves de API manualmente:" -ForegroundColor Yellow
Write-Host "  [Environment]::SetEnvironmentVariable('NVIDIA_API_KEY', 'sua-chave-aqui', 'User')"
Write-Host "  [Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sua-chave-aqui', 'User')"

# ============================================================
# PASSO 4: Clonar repositorio
# ============================================================
Step "4/6 - Clonando repositorio do ecossistema"

if (Test-Path "$InstallDir\.git") {
    Write-Host "Repo ja existe em $InstallDir. Atualizando..." -ForegroundColor Yellow
    Push-Location $InstallDir
    git pull origin $Branch
    Pop-Location
} else {
    if (Test-Path $InstallDir) {
        Remove-Item -Recurse -Force $InstallDir -ErrorAction SilentlyContinue
    }
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    git clone --branch $Branch --single-branch $RepoUrl $InstallDir
    CheckSuccess "Clone em $InstallDir"
}

# ============================================================
# PASSO 5: Executar setup completo
# ============================================================
Step "5/6 - Executando setup do ecossistema"

& "$InstallDir\setup.ps1" -VaultPath $VaultPath -InstallDir $InstallDir -SkipClone:$true
CheckSuccess "Setup concluido"

# ============================================================
# PASSO 6: Verificacao final
# ============================================================
Step "6/6 - Verificacao final"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  ECOSSISTEMA INSTALADO COM SUCESSO!" -ForegroundColor White -BackgroundColor DarkGreen
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nProximos passos:"
Write-Host "  1. Configure as chaves de API (veja passo 3)"
Write-Host "  2. Abra o OpenCode:  opencode"
Write-Host "  3. Teste o LER:      ler --status"
Write-Host "  4. Execute:          ler --audit"
Write-Host "`nComando unico para ja começar:" -ForegroundColor Cyan
Write-Host "  opencode" -ForegroundColor White
Write-Host "`nInstalado em:     $InstallDir"
Write-Host "Vault em:         $VaultPath"
Write-Host "Config OpenCode:  $env:USERPROFILE\.config\opencode\opencode.jsonc"