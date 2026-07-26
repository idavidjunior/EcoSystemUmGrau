<#
.SYNOPSIS
    Configura o ecossistema LER + OpenCode + Obsidian + Ponytail em uma maquina nova.
.DESCRIPTION
    Clona o repo, instala dependencias, gera opencode.json, copia skills,
    cria vault, inicializa governance, e verifica tudo.
.PARAMETER RepoUrl
    URL do repositorio GitHub (default: https://github.com/idavidjunior/WindowsMaintenanceSuite_v3.git)
.PARAMETER Branch
    Branch do repositorio (default: opencode/mighty-meadow)
.PARAMETER VaultPath
    Caminho para o vault Obsidian (default: ~/Desktop/Codigos)
.PARAMETER InstallDir
    Onde clonar o repositorio (default: ~/.local/share/opencode/worktree/mighty-meadow)
.PARAMETER SkipClone
    Pula o clone se o repo ja existe
.EXAMPLE
    .\setup.ps1 -VaultPath "C:\Users\Fulano\Desktop\MeuVault"
.EXAMPLE
    .\setup.ps1 -InstallDir "D:\Projetos\MeuEcossistema" -SkipClone:$false
#>

param(
    [string]$RepoUrl = "https://github.com/idavidjunior/EcoSystemUmGrau.git",
    [string]$Branch = "opencode/mighty-meadow",
    [string]$VaultPath = "$env:USERPROFILE\Desktop\Codigos",
    [string]$InstallDir = "$env:LOCALAPPDATA\opencode\worktree\mighty-meadow",
    [switch]$SkipClone = $false
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Setup Ecossistema LER v2.0"

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
Step "1/8 - Verificando pre-requisitos"

$prereqs = @(
    @{Name="Git"; Cmd="git --version"},
    @{Name="Node.js 18+"; Cmd="node --version"},
    @{Name="Python 3.8+"; Cmd="python --version"},
    @{Name="PowerShell 5.1+"; Cmd="powershell -Command `$PSVersionTable.PSVersion"}
)

foreach ($p in $prereqs) {
    try {
        $out = cmd /c "$($p.Cmd) 2>&1"
        Write-Host "  [OK] $($p.Name): $($out -join '')" -ForegroundColor Green
    } catch {
        Write-Host "  [FALTA] $($p.Name) - Instale antes de prosseguir" -ForegroundColor Red
        exit 1
    }
}

# ============================================================
# PASSO 2: Clonar repositorio
# ============================================================
Step "2/8 - Obtendo repositorio"

if ($SkipClone -and (Test-Path "$InstallDir\.git")) {
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
    CheckSuccess "Clone do repositorio em $InstallDir"
}

$REPO_DIR = $InstallDir -replace '\\', '\\'
$SKILLS_DIR = "$env:USERPROFILE\.claude\skills"
$OPENCODE_CONFIG = "$env:USERPROFILE\.config\opencode"

# ============================================================
# PASSO 3: Skills
# ============================================================
Step "3/8 - Instalando skills"

$neededSkills = @("android-pure-sdk", "mp3player-metadata-rescue", "ler")
$skillsRepo = "$InstallDir\skills"

if (Test-Path $skillsRepo) {
    # Skills embutidas no repo
    New-Item -ItemType Directory -Force -Path $SKILLS_DIR | Out-Null
    foreach ($s in $neededSkills) {
        $src = "$skillsRepo\$s\SKILL.md"
        $dst = "$SKILLS_DIR\$s"
        if (Test-Path $src) {
            New-Item -ItemType Directory -Force -Path $dst | Out-Null
            Copy-Item "$skillsRepo\$s\*" "$dst\" -Recurse -Force
            Write-Host "  [OK] Skill '$s' copiada do repo" -ForegroundColor Green
        } else {
            Write-Host "  [AVISO] Skill '$s' nao encontrada no repo. Baixando..." -ForegroundColor Yellow
            $url = "https://raw.githubusercontent.com/idavidjunior/WindowsMaintenanceSuite_v3/$Branch/skills/$s/SKILL.md"
            New-Item -ItemType Directory -Force -Path $dst | Out-Null
            try { Invoke-WebRequest -Uri $url -OutFile "$dst\SKILL.md" -UseBasicParsing -ErrorAction Stop
                  Write-Host "  [OK] Skill '$s' baixada" -ForegroundColor Green } catch {
                Write-Host "  [AVISO] Nao foi possivel baixar skill '$s'. Crie manualmente." -ForegroundColor Yellow
            }
        }
    }
} else {
    # Skills estao localmente apenas
    Write-Host "Skills ja existentes em $SKILLS_DIR" -ForegroundColor Green
}

# Reference skills/custom from repo if available
$customSkills = "$InstallDir\skills"
if (Test-Path $customSkills) {
    $SKILLS_DIR = $customSkills
    Write-Host "Usando skills do repositorio: $customSkills" -ForegroundColor Cyan
}

# ============================================================
# PASSO 4: Ponytail
# ============================================================
Step "4/8 - Instalando Ponytail"

$pluginDir = "$OPENCODE_CONFIG\plugin"
New-Item -ItemType Directory -Force -Path $pluginDir | Out-Null

$ponytailUrl = "https://raw.githubusercontent.com/DietrichGebert/ponytail/main/.opencode/plugins/ponytail.mjs"
$ponytailPath = "$pluginDir\ponytail.mjs"

try {
    Invoke-WebRequest -Uri $ponytailUrl -OutFile $ponytailPath -UseBasicParsing -ErrorAction Stop
    CheckSuccess "Ponytail baixado ($((Get-Item $ponytailPath).Length) bytes)"
} catch {
    Write-Host "[FALHA] Nao foi possivel baixar Ponytail. Verifique internet." -ForegroundColor Red
    exit 1
}

# ============================================================
# PASSO 5: Copiar vault do repositorio
# ============================================================
Step "5/8 - Copiando vault (notas + docs do ecossistema)"

$repoVault = "$InstallDir\vault"
if (Test-Path $repoVault) {
    Write-Host "Copiando vault do repositorio para $VaultPath ..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Force -Path $VaultPath | Out-Null
    cmd /c "robocopy `"$repoVault`" `"$VaultPath`" /MIR /NDL /NFL /NJH /NJS /R:0 /W:0 /xd `.git 2>&1" | Out-Null

    $count = (Get-ChildItem $VaultPath -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
    CheckSuccess "Vault copiado: $count arquivos em $VaultPath"
} else {
    Write-Host "[AVISO] Nenhum vault no repositorio. Criando vault vazio..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $VaultPath | Out-Null
}

# Criar .obsidian se nao existir
$obsidianDir = "$VaultPath\.obsidian"
if (-not (Test-Path $obsidianDir)) {
    New-Item -ItemType Directory -Force -Path $obsidianDir | Out-Null
    @{workspace = "main"} | ConvertTo-Json | Set-Content "$obsidianDir\workspace.json" -Encoding UTF8
    @{theme = "moonstone"} | ConvertTo-Json | Set-Content "$obsidianDir\appearance.json" -Encoding UTF8
}

# ============================================================
# PASSO 6: Instalar MCPVault
# ============================================================
# ============================================================
# PASSO 6a: Instalar Watch-Vault (Watcher automatico)
# ============================================================
Step "6a/9 - Instalando Watch-Vault (monitor+sync+notificacao)"

$watcherScript = "$InstallDir\watch-vault.ps1"
$installerScript = "$InstallDir\install-watcher.ps1"

if (Test-Path $watcherScript -and (Test-Path $installerScript)) {
    Write-Host "Instalando watcher como servico Windows..." -ForegroundColor Cyan
    & $installerScript
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        Write-Host "[AVISO] Watcher pode nao ter instalado corretamente." -ForegroundColor Yellow
        Write-Host "  Execute manualmente: $installerScript" -ForegroundColor Yellow
    }
} else {
    Write-Host "[AVISO] Scripts do watcher nao encontrados. Instale manualmente:" -ForegroundColor Yellow
    Write-Host "  .\install-watcher.ps1" -ForegroundColor Yellow
}

Write-Host "`nWatcher configurado: inicia automaticamente no login." -ForegroundColor Green
Write-Host "  - Monitora alteracoes no vault"
Write-Host "  - Sincroniza automaticamente com GitHub"
Write-Host "  - Exibe popup + som a cada sincronizacao"

# ============================================================
# PASSO 6b: Instalar MCPVault
# ============================================================
Step "7/9 - Instalando MCPVault"

Write-Host "Testando @bitbonsai/mcpvault..." -ForegroundColor Cyan
$mcpTest = cmd /c "npx @bitbonsai/mcpvault --version 2>&1"
if ($mcpTest -match "\d+\.\d+\.\d+") {
    CheckSuccess "MCPVault $($mcpTest -replace '\s','') disponivel"
} else {
    Write-Host "[FALHA] Nao foi possivel instalar MCPVault. Execute manualmente:" -ForegroundColor Red
    Write-Host "  npx @bitbonsai/mcpvault --version" -ForegroundColor Yellow
    exit 1
}

# ============================================================
# PASSO 6: Gerar opencode.jsonc
# ============================================================
Step "8/9 - Gerando opencode.jsonc"

$templatePath = "$InstallDir\opencode.template.json"
$outputPath = "$OPENCODE_CONFIG\opencode.jsonc"

if (-not (Test-Path $templatePath)) {
    Write-Host "[FALHA] Template nao encontrado em $templatePath" -ForegroundColor Red
    exit 1
}

$content = Get-Content $templatePath -Raw -Encoding UTF8
$content = $content -replace "{{SKILLS_DIR}}", $SKILLS_DIR
$content = $content -replace "{{REPO_DIR}}", $REPO_DIR
$content = $content -replace "{{VAULT_PATH}}", $VaultPath

New-Item -ItemType Directory -Force -Path "$OPENCODE_CONFIG" | Out-Null
$content | Set-Content $outputPath -Encoding UTF8
CheckSuccess "opencode.jsonc gerado em $outputPath"

Write-Host "`nConteudo gerado:" -ForegroundColor Cyan
Write-Host "  SKILLS_DIR -> $SKILLS_DIR"
Write-Host "  OPENCODE_CONFIG -> $OPENCODE_CONFIG"
Write-Host "  REPO_DIR -> $REPO_DIR"
Write-Host "  VAULT_PATH -> $VaultPath"
Write-Host "  PLUGIN (instalado, nao referenciado no JSON) -> $OPENCODE_CONFIG\plugin\ponytail.mjs"

# ============================================================
# PASSO 8: Inicializar LER Governance
# ============================================================
Step "9/9 - Inicializando LER Governance"

$govDir = "$InstallDir\LoopEngineeringAgent\memory\governance"
New-Item -ItemType Directory -Force -Path $govDir | Out-Null

# Testar se Python consegue importar os modulos LER
Write-Host "Testando modulos LER..." -ForegroundColor Cyan
$lerTest = python -c "
import sys
sys.path.insert(0, r'$InstallDir\LoopEngineeringAgent')
from governance.agent_governance import AgentGovernance
from governance.conflict_detector import ConflictDetector
print('LER modules: OK')
" 2>&1

if ($lerTest -match "OK") {
    CheckSuccess "Modulos LER carregam sem erros"
} else {
    Write-Host "[AVISO] $lerTest" -ForegroundColor Yellow
    Write-Host "  (pode ignorar se planeja usar LER via OpenCode Bridge)" -ForegroundColor Yellow
}

# ============================================================
# PASSO 9: Verificacao final
# ============================================================
Step "10/10 - Verificacao final"

$checks = @(
    @{Desc="Repositorio clonado"; Path="$InstallDir\.git"},
    @{Desc="Ponytail instalado"; Path=$ponytailPath},
    @{Desc="opencode.jsonc gerado"; Path=$outputPath},
    @{Desc="Vault existe"; Path=$VaultPath},
    @{Desc="Vault .obsidian"; Path=$obsidianDir},
    @{Desc="LER governance"; Path="$InstallDir\LoopEngineeringAgent\governance\responsibility_map.json"},
    @{Desc="LER vault bridge"; Path="$InstallDir\LoopEngineeringAgent\governance\vault_bridge.py"},
    @{Desc="MCP server"; Path="$InstallDir\LoopEngineeringAgent\integrations\opencode\provider_mcp_server.py"},
    @{Desc="Watch-Vault script"; Path=$watcherScript},
    @{Desc="Watch-Vault installer"; Path=$installerScript}
)

$allOk = $true
foreach ($c in $checks) {
    if (Test-Path $c.Path) {
        Write-Host "  [OK] $($c.Desc)" -ForegroundColor Green
    } else {
        Write-Host "  [FALTA] $($c.Desc) em $($c.Path)" -ForegroundColor Red
        $allOk = $false
    }
}

# Testar MCPVault
Write-Host "`nTestando MCPVault..." -ForegroundColor Cyan
$mcpPayload = '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_directory","arguments":{}}}'
$mcpResult = $mcpPayload | & "npx.cmd" "@bitbonsai/mcpvault" "$VaultPath" 2>&1
if ($mcpResult -match "dirs") {
    CheckSuccess "MCPVault respondendo (vault acessivel)"
} else {
    Write-Host "[AVISO] MCPVault nao respondeu. Verifique se o vault path esta correto." -ForegroundColor Yellow
}

# Verificar watcher
try {
    $watcherTask = Get-ScheduledTask -TaskName "VaultAutoSyncWatcher" -ErrorAction Stop
    Write-Host "  [OK] Watch-Vault instalado como servico ($($watcherTask.State))" -ForegroundColor Green
} catch {
    Write-Host "  [AVISO] Watch-Vault nao instalado como servico" -ForegroundColor Yellow
    Write-Host "    Execute: .\install-watcher.ps1" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
if ($allOk) {
    Write-Host "  ECOSSISTEMA INSTALADO COM SUCESSO!" -ForegroundColor White -BackgroundColor DarkGreen
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "`nProximos passos:"
    Write-Host "  1. Abra o OpenCode e inicie uma sessao"
    Write-Host "  2. Verifique se Ponytail aparece nos logs de inicializacao"
    Write-Host "  3. Execute: ler --status  (para testar LER)"
    Write-Host "  4. Execute: ler --audit  (para auditar o projeto)"
    Write-Host "`nPara usar o LER com o OpenCode:"
    Write-Host "  ler ""minha missao aqui"""
    Write-Host "`nPara ver o ecossistema completo no vault:"
    Write-Host "  vault note: LER/EcossistemaAgentes.md"
    Write-Host "`nArquivos importantes:"
    Write-Host "  Config:        $outputPath (formato restrito — sem plugins)"
    Write-Host "  Repo:          $InstallDir"
    Write-Host "  Vault:         $VaultPath"
    Write-Host "  Governance:    $InstallDir\LoopEngineeringAgent\governance\responsibility_map.json"
} else {
    Write-Host "  INSTALACAO INCOMPLETA - verifique os itens FALTA acima" -ForegroundColor White -BackgroundColor DarkRed
}
