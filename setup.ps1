<#
.SYNOPSIS
    Configura o ecossistema LER + OpenCode + Obsidian em Desktop/Codigos/EcoSystemUmGrau/.
.DESCRIPTION
    Verifica pre-requisitos, gera opencode.jsonc com skills unificadas,
    configura vault Obsidian, instala Ponytail, MCPVault, watcher,
    e inicializa LER Governance.
.PARAMETER VaultPath
    Caminho do vault (default: ~/Desktop/Codigos/EcoSystemUmGrau)
.PARAMETER InstallDir
    Onde o repo esta clonado (default: ~/Desktop/Codigos/EcoSystemUmGrau)
.PARAMETER SkipClone
    Pula o clone se o repo ja existe
#>

param(
    [string]$VaultPath = "$env:USERPROFILE\Desktop\Codigos\EcoSystemUmGrau",
    [string]$InstallDir = "$env:USERPROFILE\Desktop\Codigos\EcoSystemUmGrau",
    [switch]$SkipClone = $false
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Setup Ecossistema LER v2.0"
$OPENCODE_CONFIG = "$env:USERPROFILE\.config\opencode"

function Step($title) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host ">>> $title" -ForegroundColor White -BackgroundColor DarkBlue
    Write-Host "========================================" -ForegroundColor Cyan
}
function CheckSuccess($desc) {
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { Write-Host "[FALHA] $desc" -ForegroundColor Red; exit 1 }
    Write-Host "[OK] $desc" -ForegroundColor Green
}

# ============================================================
# PASSO 1: Pre-requisitos
# ============================================================
Step "1/8 - Verificando pre-requisitos"
$prereqs = @(
    @{Name="Git"; Cmd="git --version"},
    @{Name="Node.js 18+"; Cmd="node --version"},
    @{Name="Python 3.8+"; Cmd="python --version"},
    @{Name="PowerShell 5.1+"; Cmd="powershell -Command `$PSVersionTable.PSVersion"}
)
foreach ($p in $prereqs) {
    try { $out = cmd /c "$($p.Cmd) 2>&1"; Write-Host "  [OK] $($p.Name): $($out -join '')" -ForegroundColor Green }
    catch { Write-Host "  [FALTA] $($p.Name) - Instale antes" -ForegroundColor Red; exit 1 }
}

# ============================================================
# PASSO 2: Repositorio
# ============================================================
Step "2/8 - Verificando repositorio"
if (-not (Test-Path "$InstallDir\.git")) {
    Write-Host "[FALTA] Repo nao encontrado em $InstallDir. Execute bootstrap.ps1 primeiro." -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] Repositorio em $InstallDir" -ForegroundColor Green

$REPO_DIR = $InstallDir -replace '\\', '\\'
$SKILLS_DIR = "$InstallDir\skills"

# ============================================================
# PASSO 3: Skills unificadas
# ============================================================
Step "3/8 - Skills unificadas"
if (Test-Path $SKILLS_DIR) {
    $count = (Get-ChildItem $SKILLS_DIR -Directory).Count
    Write-Host "  [OK] $count skills encontradas em $SKILLS_DIR" -ForegroundColor Green
} else {
    Write-Host "  [AVISO] Diretorio de skills nao encontrado em $SKILLS_DIR" -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $SKILLS_DIR | Out-Null
}

# ============================================================
# PASSO 4: Ponytail
# ============================================================
Step "4/8 - Instalando Ponytail"
$pluginDir = "$OPENCODE_CONFIG\plugin"
New-Item -ItemType Directory -Force -Path $pluginDir | Out-Null
$ponytailUrl = "https://raw.githubusercontent.com/DietrichGeber/ponytail/main/.opencode/plugins/ponytail.mjs"
$ponytailPath = "$pluginDir\ponytail.mjs"
try {
    Invoke-WebRequest -Uri $ponytailUrl -OutFile $ponytailPath -UseBasicParsing -ErrorAction Stop
    CheckSuccess "Ponytail baixado ($((Get-Item $ponytailPath).Length) bytes)"
} catch {
    Write-Host "[FALHA] Nao foi possivel baixar Ponytail." -ForegroundColor Red; exit 1
}

# ============================================================
# PASSO 5: Vault Obsidian
# ============================================================
Step "5/8 - Configurando vault Obsidian"
New-Item -ItemType Directory -Force -Path $VaultPath | Out-Null

# Copiar vault notes se existirem
$repoVault = "$InstallDir\vault"
if (Test-Path $repoVault) {
    Write-Host "Copiando vault notes..." -ForegroundColor Cyan
    cmd /c "robocopy `"$repoVault`" `"$VaultPath`" /MIR /NDL /NFL /NJH /NJS /R:0 /W:0 /xd `.git 2>&1" | Out-Null
    $count = (Get-ChildItem $VaultPath -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
    Write-Host "  [OK] $count arquivos no vault" -ForegroundColor Green
}

# .obsidian ja existe no repo (vem no git)
$obsidianDir = "$VaultPath\.obsidian"
if (-not (Test-Path $obsidianDir)) {
    New-Item -ItemType Directory -Force -Path $obsidianDir | Out-Null
    @{workspace = "main"} | ConvertTo-Json | Set-Content "$obsidianDir\workspace.json" -Encoding UTF8
    @{theme = "moonstone"} | ConvertTo-Json | Set-Content "$obsidianDir\appearance.json" -Encoding UTF8
    Write-Host "  [OK] .obsidian criado" -ForegroundColor Green
} else {
    Write-Host "  [OK] .obsidian ja existe" -ForegroundColor Green
}

# ============================================================
# PASSO 6: Watch-Vault
# ============================================================
Step "6/8 - Instalando Watch-Vault"
$watcherScript = "$InstallDir\watch-vault.ps1"
$installerScript = "$InstallDir\install-watcher.ps1"
if (Test-Path $watcherScript -and (Test-Path $installerScript)) {
    Write-Host "Instalando watcher..." -ForegroundColor Cyan
    & $installerScript
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        Write-Host "[AVISO] Watcher nao instalou. Execute manualmente: $installerScript" -ForegroundColor Yellow
    }
} else {
    Write-Host "[AVISO] Scripts watcher nao encontrados." -ForegroundColor Yellow
}

# ============================================================
# PASSO 7: Gerar opencode.jsonc
# ============================================================
Step "7/8 - Gerando opencode.jsonc"
$templatePath = "$InstallDir\opencode.template.json"
$outputPath = "$OPENCODE_CONFIG\opencode.jsonc"

if (-not (Test-Path $templatePath)) { Write-Host "[FALHA] Template nao encontrado" -ForegroundColor Red; exit 1 }

$content = Get-Content $templatePath -Raw -Encoding UTF8
$content = $content -replace "{{SKILLS_DIR}}", $SKILLS_DIR
$content = $content -replace "{{REPO_DIR}}", $REPO_DIR
$content = $content -replace "{{VAULT_PATH}}", $VaultPath

New-Item -ItemType Directory -Force -Path "$OPENCODE_CONFIG" | Out-Null
$content | Set-Content $outputPath -Encoding UTF8
CheckSuccess "opencode.jsonc gerado em $outputPath"
Write-Host "  SKILLS_DIR -> $SKILLS_DIR" -ForegroundColor Cyan
Write-Host "  REPO_DIR -> $REPO_DIR" -ForegroundColor Cyan
Write-Host "  VAULT_PATH -> $VaultPath" -ForegroundColor Cyan

# ============================================================
# PASSO 8: Inicializar LER Governance
# ============================================================
Step "8/8 - Inicializando LER Governance"
$govDir = "$InstallDir\LoopEngineeringAgent\memory\governance"
New-Item -ItemType Directory -Force -Path $govDir | Out-Null

Write-Host "Testando modulos LER..." -ForegroundColor Cyan
$lerTest = python -c "
import sys
sys.path.insert(0, r'$InstallDir\LoopEngineeringAgent')
from governance.agent_governance import AgentGovernance
from governance.conflict_detector import ConflictDetector
print('LER modules: OK')
" 2>&1

if ($lerTest -match "OK") { CheckSuccess "Modulos LER carregam sem erros" }
else { Write-Host "[AVISO] $lerTest" -ForegroundColor Yellow }

# ============================================================
# VERIFICACAO FINAL
# ============================================================
Write-Host "`n========================================" -ForegroundColor Cyan

$checks = @(
    @{Desc="Repositorio clonado"; Path="$InstallDir\.git"},
    @{Desc="Skills unificadas"; Path=$SKILLS_DIR},
    @{Desc="Ponytail instalado"; Path=$ponytailPath},
    @{Desc="opencode.jsonc gerado"; Path=$outputPath},
    @{Desc="Vault .obsidian"; Path=$obsidianDir},
    @{Desc="LER governance"; Path="$InstallDir\LoopEngineeringAgent\governance\responsibility_map.json"},
    @{Desc="LER vault bridge"; Path="$InstallDir\LoopEngineeringAgent\governance\vault_bridge.py"},
    @{Desc="MCP server"; Path="$InstallDir\LoopEngineeringAgent\integrations\opencode\provider_mcp_server.py"},
    @{Desc="Watch-Vault script"; Path=$watcherScript}
)
$allOk = $true
foreach ($c in $checks) {
    if (Test-Path $c.Path) { Write-Host "  [OK] $($c.Desc)" -ForegroundColor Green }
    else { Write-Host "  [FALTA] $($c.Desc)" -ForegroundColor Red; $allOk = $false }
}

if ($allOk) {
    Write-Host "`n  ECOSSISTEMA INSTALADO COM SUCESSO!" -ForegroundColor White -BackgroundColor DarkGreen
    Write-Host "`nProximos passos:" -ForegroundColor Cyan
    Write-Host "  1. Abra o OpenCode e inicie uma sessao"
    Write-Host "  2. Execute: ler --status"
    Write-Host "  3. Para usar LER com OpenCode: ler ""minha missao aqui"""
    Write-Host "`nConfig:  $outputPath"
    Write-Host "Repo:    $InstallDir"
    Write-Host "Vault:   $VaultPath"
} else {
    Write-Host "`n  INSTALACAO INCOMPLETA" -ForegroundColor White -BackgroundColor DarkRed
}
