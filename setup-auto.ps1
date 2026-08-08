#!/usr/bin/env pwsh
<#
.SYNOPSIS
    EcoSystemUmGrau - Setup Plug & Play AUTOMÁTICO (sem prompts interativos).

.DESCRIPTION
    Clone ou atualiza tudo, instala OpenCode + plugin fallback, deploy de config,
    instala dependências Python e configura tudo em um novo PC.
    
    Uso:
      powershell -ExecutionPolicy Bypass -File setup-auto.ps1
      powershell -ExecutionPolicy Bypass -File setup-auto.ps1 -SkipGitAuth
      powershell -ExecutionPolicy Bypass -File setup-auto.ps1 -Force

.PARAMETER SkipGitAuth
    Pula autenticação Git/GitHub (para ambientes onde o token não está disponível).

.PARAMETER Force
    Força re-instalação mesmo se já existir.

.EXAMPLE
    # Setup completo automático:
    powershell -ExecutionPolicy Bypass -File setup-auto.ps1
    
    # Se já tem ecossistema clonado, só faz sync:
    powershell -ExecutionPolicy Bypass -File setup-auto.ps1 -SyncOnly
#>
param(
    [switch]$SkipGitAuth = $false,
    [switch]$Force = $false,
    [switch]$SyncOnly = $false
)

$ErrorActionPreference = "Stop"
$ECO_DIR = "$env:USERPROFILE\Documents\Default Project\EcoSystemUmGrau"
$LER_DIR = "$ECO_DIR\ler-runtime"
$OCODE_DIR = "$env:USERPROFILE\.config\opencode"
$AGENTS_SRC = "$ECO_DIR\config\agents"
$PROFILE_DIR = "$env:USERPROFILE\Documents\WindowsPowerShell"
$PROFILE_PS1 = "$PROFILE_DIR\profile.ps1"

function Write-Step { param($Msg) Write-Host "`n>>> $Msg" -ForegroundColor Cyan }
function Write-OK   { param($Msg) Write-Host "  [OK] $Msg" -ForegroundColor Green }
function Write-Info { param($Msg) Write-Host "  [..] $Msg" -ForegroundColor Gray }
function Write-Err  { param($Msg) Write-Host "  [!!] $Msg" -ForegroundColor Red }

Write-Host @"
====================================================
  EcoSystemUmGrau - Setup AUTOMATICO (Plug & Play)
  Repo: https://github.com/idavidjunior/EcoSystemUmGrau
====================================================
"@ -ForegroundColor Cyan

# ─── 0. Verificar requisitos ──────────────────────
Write-Step "[0/9] Verificando requisitos"

$missing = @()
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { $missing += "Git" }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { $missing += "Node.js" }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { $missing += "Python" }

if ($missing.Count -gt 0) {
    Write-Err "Faltando: $($missing -join ', ')"
    Write-Host "Instale de:" -ForegroundColor Yellow
    Write-Host "  Git:     https://git-scm.com/" -ForegroundColor Yellow
    Write-Host "  Node.js: https://nodejs.org/" -ForegroundColor Yellow
    Write-Host "  Python:  https://python.org/" -ForegroundColor Yellow
    exit 1
}
Write-OK "Git, Node.js, Python detectados"

# ─── 1. Clonar ou atualizar EcoSystemUmGrau ──────
Write-Step "[1/9] EcoSystemUmGrau"

if ($SyncOnly -and (Test-Path "$ECO_DIR\.git")) {
    Write-Info "Modo sync-only"
    Push-Location $ECO_DIR
    git pull --ff-only 2>&1 | ForEach-Object { Write-Info $_ }
    Pop-Location
    Write-OK "EcoSystemUmGrau atualizado"
}
elseif (Test-Path "$ECO_DIR\.git") {
    if ($Force) {
        Write-Info "Force: reclonando..."
        Remove-Item $ECO_DIR -Recurse -Force
    }
    else {
        Write-Info "Ja clonado, atualizando..."
        Push-Location $ECO_DIR
        git pull --ff-only 2>&1 | ForEach-Object { Write-Info $_ }
        Pop-Location
        Write-OK "EcoSystemUmGrau atualizado"
    }
}
else {
    Write-Info "Clonando do GitHub..."
    if (-not (Test-Path (Split-Path $ECO_DIR))) {
        New-Item -ItemType Directory -Path (Split-Path $ECO_DIR) -Force | Out-Null
    }
    
    if (-not $SkipGitAuth) {
        # Tenta clonar usando token do ambiente ou GH CLI
        $ghToken = $env:GH_TOKEN
        if (Get-Command gh -ErrorAction SilentlyContinue) {
            git clone "https://github.com/idavidjunior/EcoSystemUmGrau.git" "$ECO_DIR" 2>&1 | ForEach-Object { Write-Info $_ }
        }
        else {
            git clone "https://github.com/idavidjunior/EcoSystemUmGrau.git" "$ECO_DIR" 2>&1 | ForEach-Object { Write-Info $_ }
        }
    }
    else {
        git clone "https://github.com/idavidjunior/EcoSystemUmGrau.git" "$ECO_DIR" 2>&1 | ForEach-Object { Write-Info $_ }
    }
    Write-OK "EcoSystemUmGrau clonado"
}

# ─── 2. Instalar OpenCode ──────────────────────────
Write-Step "[2/9] OpenCode"
npm list -g opencode-ai >$null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Info "Instalando OpenCode..."
    npm i -g opencode-ai 2>&1 | ForEach-Object { Write-Info $_ }
    Write-OK "OpenCode instalado"
} else {
    Write-OK "OpenCode ja instalado"
}

# ─── 3. Deploy config OpenCode ────────────────────
Write-Step "[3/9] Config OpenCode"

Push-Location $ECO_DIR
$up = $env:USERPROFILE.Replace('\', '/')

# Sincroniza 3 camadas de regras
Write-Info "Sync de regras..."
python scripts\sync_rules.py update 2>&1 | ForEach-Object { Write-Info $_ }

# Gera opencode.jsonc do template
if (-not (Test-Path $OCODE_DIR)) { New-Item -ItemType Directory -Path $OCODE_DIR -Force | Out-Null }
if (-not (Test-Path "$OCODE_DIR\agents")) { New-Item -ItemType Directory -Path "$OCODE_DIR\agents" -Force | Out-Null }

$template = Get-Content "$ECO_DIR\config\opencode.jsonc" -Raw
$rendered = $template.Replace('{{USERPROFILE}}', $up)
Set-Content "$OCODE_DIR\opencode.jsonc" -Value $rendered -Encoding UTF8 -Force
Write-OK "opencode.jsonc deployado"

# Fallback config
Copy-Item "$ECO_DIR\config\opencode-model-fallback.jsonc" "$OCODE_DIR\" -Force -ErrorAction SilentlyContinue
Write-OK "opencode-model-fallback.jsonc copiado"

# Agents
Copy-Item "$AGENTS_SRC\*.md" "$OCODE_DIR\agents\" -Force -ErrorAction SilentlyContinue
Write-OK "Agents deployados ($(Get-ChildItem "$OCODE_DIR\agents\*.md" | Measure-Object | Select-Object -ExpandProperty Count))"

# Plugin fallback
$fbDir = "$OCODE_DIR\node_modules"
if (-not (Test-Path "$fbDir\@razroo\opencode-model-fallback")) {
    Write-Info "Instalando plugin fallback..."
    if (-not (Test-Path $fbDir)) { New-Item -ItemType Directory -Path $fbDir -Force | Out-Null }
    Push-Location $fbDir
    npm init -y >$null 2>&1
    npm install @razroo/opencode-model-fallback 2>&1 | ForEach-Object { Write-Info $_ }
    Pop-Location
}
Write-OK "Plugin fallback OK"

# Valida
$test = & opencode debug config --pure 2>&1 | Out-String
if ($test -match "Error|Invalid") {
    Write-Err "Config invalida: $($test | Select-String 'Error|Invalid' | Select-Object -First 1)"
} else {
    Write-OK "Config OpenCode valida"
}
Pop-Location

# ─── 4. Python dependencies ────────────────────────
Write-Step "[4/9] Dependencias Python"

Push-Location $ECO_DIR
$requirements = @(
    "dspy-ai",
    "edge-tts",
    "httpx",
    "websockets",
    "requests",
    "pyyaml",
    "tiktoken",
    "openai",
)

foreach ($pkg in $requirements) {
    $installed = pip show $pkg 2>$null | Select-String "Version"
    if ($installed) {
        Write-Info "$pkg: $($installed.Line)"
    }
    else {
        Write-Info "Instalando $pkg..."
        pip install $pkg --quiet 2>&1 | ForEach-Object { Write-Info $_ }
    }
}
Write-OK "Dependencias Python instaladas"
Pop-Location

# ─── 5. LER runtime ─────────────────────────────────
Write-Step "[5/9] LER Runtime"
if (Test-Path "$LER_DIR\run.py") {
    Write-OK "LER runtime presente"
} else {
    Write-Info "LER runtime nao encontrado (normal se nao usa LER)"
}

# ─── 6. Profile PowerShell ──────────────────────────
Write-Step "[6/9] Profile PowerShell"
if (-not (Test-Path $PROFILE_DIR)) { New-Item -ItemType Directory -Path $PROFILE_DIR -Force | Out-Null }

if (-not (Test-Path $PROFILE_PS1)) {
    New-Item -ItemType File -Path $PROFILE_PS1 -Force | Out-Null
}

$profileContent = Get-Content $PROFILE_PS1 -Raw -ErrorAction SilentlyContinue
if (-not ($profileContent -match "EcoSystemUmGrau")) {
    $functions = @"

# ============================================================
# EcoSystemUmGrau - Gerado por setup-auto.ps1
# ============================================================
`$env:EcoSystemUmGrau = "$ECO_DIR"

function start-vigilante {
    `$script = "$ECO_DIR\scripts\vigilante.ps1"
    if (Test-Path `$script) { Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$script`"" -WindowStyle Hidden }
    else { Write-Host "[ERRO] vigilante.ps1 nao encontrado" -ForegroundColor Red }
}
function stop-vigilante  { powershell -NoProfile -ExecutionPolicy Bypass -File "$ECO_DIR\scripts\vigilante.ps1" -Stop }
function status-vigilante { powershell -NoProfile -ExecutionPolicy Bypass -File "$ECO_DIR\scripts\vigilante.ps1" -Status }
function ecosystem {
    `$script = "$ECO_DIR\scripts\ecosystem.ps1"
    if (Test-Path `$script) { & `$script @args }
    else { Write-Host "[ERRO] ecosystem.ps1 nao encontrado" -ForegroundColor Red }
}
function otimizar {
    `$script = "$ECO_DIR\scripts\prompt_optimizer_cli.py"
    if (Test-Path `$script) { & `$script @args }
}
function @eco     { ecosystem sync; python "$ECO_DIR\scripts\runtime_boot.py" }
function @sync    { ecosystem sync }
"@
    # Convert to script block format  
    $functions | Out-File -FilePath $PROFILE_PS1 -Append -Encoding UTF8
    Write-OK "Funcoes PowerShell adicionadas"
} else {
    Write-OK "Profile ja configurado"
}

# ─── 7. Scheduled Task ─────────────────────────────
Write-Step "[7/9] Scheduled Task"
$taskName = "EcoSystemVigilante"
$taskExists = schtasks /Query /TN $taskName 2>$null
if (-not $taskExists) {
    powershell -NoProfile -Command @"
`$a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File '$ECO_DIR\scripts\vigilante.ps1'";
`$t = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME;
`$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Days 3650);
Register-ScheduledTask -TaskName '$taskName' -Action `$a -Trigger `$t -Settings `$s -Force | Out-Null
"@
    if ($LASTEXITCODE -eq 0) {
        Write-OK "Scheduled Task criada"
    } else {
        Write-Err "Nao foi possivel criar a task"
    }
} else {
    Write-OK "Scheduled Task ja existe"
}

# ─── 8. API Keys (nao interativo) ───────────────────
Write-Step "[8/9] API Keys"
$keysConfigured = 0
$envKeys = @{
    "NVIDIA_API_KEY" = $env:NVIDIA_API_KEY
    "OPENAI_API_KEY" = $env:OPENAI_API_KEY
    "GH_TOKEN"       = $env:GH_TOKEN
}
foreach ($k in $envKeys.GetEnumerator()) {
    if ($k.Value) {
        $keysConfigured++
        # Salva no perfil para persistencia
        $line = "`$env:$($k.Key) = '$($k.Value)'"
        if (-not ($profileContent -match [regex]::Escape($k.Key))) {
            Add-Content $PROFILE_PS1 $line
        }
    }
}
if ($keysConfigured -eq 0) {
    Write-Info "Nenhuma API key detectada no ambiente"
    Write-Info "Configure manualmente via: setx KEY value"
} else {
    Write-OK "$keysConfigured chave(s) de API configurada(s)"
}

# ─── 9. Validar / Preflight ────────────────────────
Write-Step "[9/9] Validacao final"

Push-Location $ECO_DIR
$preflight = python scripts\preflight_check.py 2>&1 | Out-String
if ($preflight -match "TODOS TESTES PASSARAM") {
    Write-OK "Preflight: TODOS TESTES PASSARAM"
} else {
    Write-Info "Preflight: alguns testes falharam (verifique manualmente)"
}

$boot = python scripts\runtime_boot.py 2>&1 | Out-String
if ($boot -match "Integridade:  OK") {
    Write-OK "Bootloader: integridade OK"
} else {
    Write-Err "Bootloader: falhou"
}
Pop-Location

# ─── Resumo ────────────────────────────────────────
Write-Host @"
====================================================
  Setup AUTOMATICO concluido!

  EcoSystemUmGrau: $ECO_DIR
  OpenCode config: $OCODE_DIR
  Profile PS:      $PROFILE_PS1

  Comandos disponiveis:
    @eco          - Verificar/ativar EcoSystemUmGrau
    @sync         - Sincronizar tudo
    ecosystem     - Comandos do ecossistema
    start-vigilante - Iniciar vigilante (watchdog)

  Para revalidar:
    python scripts\preflight_check.py

  Repo: https://github.com/idavidjunior/EcoSystemUmGrau
====================================================
"@ -ForegroundColor Cyan
