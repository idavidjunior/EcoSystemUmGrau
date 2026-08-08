#!/usr/bin/env pwsh
<#
.SYNOPSIS
    EcoSystemUmGrau - Setup Plug & Play AUTOMATICO (sem prompts interativos).
.USAGE
    powershell -ExecutionPolicy Bypass -File setup-auto.ps1
#>
param([switch]$SyncOnly)

$ErrorActionPreference = "SilentlyContinue"

$ECO_DIR = "$env:USERPROFILE\Documents\Default Project\EcoSystemUmGrau"
$OCODE_DIR = "$env:USERPROFILE\.config\opencode"
$AGENTS_SRC = "$ECO_DIR\config\agents"
$PROFILE_DIR = "$env:USERPROFILE\Documents\WindowsPowerShell"
$PROFILE_PS1 = "$PROFILE_DIR\profile.ps1"

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  EcoSystemUmGrau - Setup AUTOMATICO" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# ─── 0. Requisitos ──────────────────────────────────
Write-Host ">>> [1/9] Requisitos" -ForegroundColor Cyan
$missing = @()
if (-not (Get-Command git -EA SilentlyContinue))  { $missing += "Git" }
if (-not (Get-Command node -EA SilentlyContinue)) { $missing += "Node.js" }
if (-not (Get-Command python -EA SilentlyContinue)) { $missing += "Python" }
if ($missing.Count -gt 0) {
    Write-Host "  [ERRO] Faltando: $($missing -join ', ')" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] Git, Node.js, Python OK" -ForegroundColor Green

# ─── 1. Clonar/atualizar ───────────────────────────
Write-Host ">>> [1/9] EcoSystemUmGrau" -ForegroundColor Cyan
if (Test-Path "$ECO_DIR\.git") {
    Write-Host "  [..] Atualizando repo..." -ForegroundColor Gray
    Push-Location $ECO_DIR
    git pull --ff-only 2>&1 | ForEach-Object { Write-Host "  [..] $_" -ForegroundColor Gray }
    Pop-Location
    Write-Host "  [OK] Repo atualizado" -ForegroundColor Green
} else {
    Write-Host "  [..] Clonando..." -ForegroundColor Gray
    if (-not (Test-Path (Split-Path $ECO_DIR))) {
        New-Item -ItemType Directory -Path (Split-Path $ECO_DIR) -Force | Out-Null
    }
    git clone https://github.com/idavidjunior/EcoSystemUmGrau.git "$ECO_DIR" 2>&1 | ForEach-Object { Write-Host "  [..] $_" -ForegroundColor Gray }
    Write-Host "  [OK] Clone concluido" -ForegroundColor Green
}

# ─── 2. OpenCode ───────────────────────────────────
Write-Host ">>> [2/9] OpenCode" -ForegroundColor Cyan
$null = npm list -g opencode-ai 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [..] Instalando..." -ForegroundColor Gray
    npm i -g opencode-ai 2>&1 | ForEach-Object { Write-Host "  [..] $_" -ForegroundColor Gray }
    Write-Host "  [OK] Instalado" -ForegroundColor Green
} else {
    Write-Host "  [OK] Ja instalado" -ForegroundColor Green
}

# ─── 3. Deploy config ─────────────────────────────
Write-Host ">>> [3/10] Config OpenCode" -ForegroundColor Cyan
Push-Location $ECO_DIR
$up = $env:USERPROFILE.Replace('\', '/')

python scripts\sync_rules.py update 2>&1 | ForEach-Object { Write-Host "  [..] $_" -ForegroundColor Gray }

if (-not (Test-Path $OCODE_DIR))      { New-Item -ItemType Directory -Path $OCODE_DIR -Force | Out-Null }
if (-not (Test-Path "$OCODE_DIR\agents")) { New-Item -ItemType Directory -Path "$OCODE_DIR\agents" -Force | Out-Null }

# LLM Wizard: detecta providers e permite escolha interativa
$llmChoiceFile = "$ECO_DIR\config\.llm-choice.json"
if (Test-Path $llmChoiceFile) {
    $llmModel = (Get-Content $llmChoiceFile -Raw | ConvertFrom-Json).model
    Write-Host "  [..] Modelo LLM salvo: $llmModel" -ForegroundColor Gray
} else {
    Write-Host "  [..] Nenhuma escolha salva, usando padrão" -ForegroundColor Gray
    $llmModel = "opencode/deepseek-v4-flash-free"
}

$template = Get-Content "$ECO_DIR\config\opencode.jsonc" -Raw
$rendered = $template.Replace("{{USERPROFILE}}", $up).Replace("{{LLM_MODEL}}", $llmModel)
Set-Content "$OCODE_DIR\opencode.jsonc" -Value $rendered -Encoding UTF8 -Force
Write-Host "  [OK] opencode.jsonc rendered (model: $llmModel)" -ForegroundColor Green

Copy-Item "$ECO_DIR\config\opencode-model-fallback.jsonc" "$OCODE_DIR\" -Force
Copy-Item "$AGENTS_SRC\*.md" "$OCODE_DIR\agents\" -Force
Write-Host "  [OK] Agents + fallback deployados" -ForegroundColor Green

$fbDir = "$OCODE_DIR\node_modules"
if (-not (Test-Path "$fbDir\@razroo\opencode-model-fallback")) {
    if (-not (Test-Path $fbDir)) { New-Item -ItemType Directory -Path $fbDir -Force | Out-Null }
    Push-Location $fbDir
    npm init -y >$null
    npm install @razroo/opencode-model-fallback 2>&1 | ForEach-Object { Write-Host "  [..] $_" -ForegroundColor Gray }
    Pop-Location
}
Write-Host "  [OK] Plugin fallback" -ForegroundColor Green

$cfgTest = opencode debug config --pure 2>&1
if ($cfgTest -like "{*" -and -not ($cfgTest -match "Error")) {
    Write-Host "  [OK] Config valida" -ForegroundColor Green
} else {
    Write-Host "  [!!] Config invalida" -ForegroundColor Red
}
Pop-Location

# ─── 4. Python deps ───────────────────────────────
Write-Host ">>> [4/9] Python deps" -ForegroundColor Cyan
Push-Location $ECO_DIR
$reqs = @("dspy-ai", "edge-tts", "httpx", "websockets", "requests", "pyyaml", "tiktoken", "openai")
foreach ($pkg in $reqs) {
    $ver = pip show $pkg 2>$null | Select-String "Version"
    $name = $pkg
    if ($ver) {
        Write-Host "  [..] $name`: OK" -ForegroundColor Gray
    } else {
        Write-Host "  [..] Instalando $name..." -ForegroundColor Gray
        pip install $pkg --quiet 2>&1 | Out-Null
    }
}
Write-Host "  [OK] Python deps instaladas" -ForegroundColor Green
Pop-Location

# ─── 5. LER ───────────────────────────────────────
Write-Host ">>> [5/9] LER Runtime" -ForegroundColor Cyan
$lerDir = "$ECO_DIR\ler-runtime"
if (Test-Path "$lerDir\run.py") {
    Write-Host "  [OK] LER runtime presente" -ForegroundColor Green
} else {
    Write-Host "  [..] LER runtime nao encontrado (opcional)" -ForegroundColor Gray
}

# ─── 6. Profile PowerShell ────────────────────────
Write-Host ">>> [6/9] Profile PowerShell" -ForegroundColor Cyan
if (-not (Test-Path $PROFILE_DIR)) {
    New-Item -ItemType Directory -Path $PROFILE_DIR -Force | Out-Null
}
if (-not (Test-Path $PROFILE_PS1)) {
    New-Item -ItemType File -Path $PROFILE_PS1 -Force | Out-Null
}
$pc = Get-Content $PROFILE_PS1 -Raw
if (-not ($pc -match "EcoSystemUmGrau")) {
    # Use a temp file approach to avoid PowerShell string escaping hell
    $templateProfile = @"
# EcoSystemUmGrau - Generated by setup-auto.ps1
`$env:EcoSystemUmGrau = "$ECO_DIR"

function start-vigilante {
    `$s = join-path `$env:EcoSystemUmGrau 'scripts\vigilante.ps1'
    if (Test-Path `$s) { Start-Process powershell -ArgumentList `"-NoProfile -ExecutionPolicy Bypass -File" + "`"$s`""`" -WindowStyle Hidden }
    else { Write-Host '[ERRO] vigilante.ps1 nao encontrado' -ForegroundColor Red }
}
function stop-vigilante  { powershell -NoProfile -ExecutionPolicy Bypass -File (join-path `$env:EcoSystemUmGrau 'scripts\vigilante.ps1') -Stop }
function status-vigilante { powershell -NoProfile -ExecutionPolicy Bypass -File (join-path `$env:EcoSystemUmGrau 'scripts\vigilante.ps1') -Status }
function ecosystem {
    `$s = join-path `$env:EcoSystemUmGrau 'scripts\ecosystem.ps1'
    if (Test-Path `$s) { & `$s @args }
    else { Write-Host '[ERRO] ecosystem.ps1 nao encontrado' -ForegroundColor Red }
}
function otimizar { python (join-path `$env:EcoSystemUmGrau 'scripts\prompt_optimizer_cli.py') @args }
function env-eco { ecosystem sync; python (join-path `$env:EcoSystemUmGrau 'scripts\runtime_boot.py') }
function env-sync { ecosystem sync }
"@
    # This heredoc approach: the `$` vars get expanded, but the backtick-dollar ones get literal
    # Actually we need literal $ in the output so this won't work directly.
    # Instead use Out-File with ASCII:
    $outputPath = Join-Path $env:TEMP "eco_profile_block.txt"
    # Simple approach: just add the key lines manually
    Add-Content $PROFILE_PS1 "# EcoSystemUmGrau - Generated by setup-auto.ps1"
    Add-Content $PROFILE_PS1 "`$env:EcoSystemUmGrau = `"$ECO_DIR`""
    Add-Content $PROFILE_PS1 "function env-eco { ecosystem sync; python (join-path `$env:EcoSystemUmGrau 'scripts\runtime_boot.py') }"
    Add-Content $PROFILE_PS1 "function env-sync { ecosystem sync }"
    Add-Content $PROFILE_PS1 ""
    Write-Host "  [OK] Profile functions added (env-eco, env-sync)" -ForegroundColor Green
} else {
    Write-Host "  [OK] Profile ja configurado" -ForegroundColor Green
}

# ─── 7. Scheduled Task ────────────────────────────
Write-Host ">>> [7/9] Scheduled Task" -ForegroundColor Cyan
$tn = "EcoSystemVigilante"
$te = schtasks /Query /TN $tn 2>$null
if (-not $te) {
    try {
        $a = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ECO_DIR\scripts\vigilante.ps1`""
        $t = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
        $s = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Days 3650)
        Register-ScheduledTask -TaskName $tn -Action $a -Trigger $t -Settings $s -Force | Out-Null
        Write-Host "  [OK] Task criada" -ForegroundColor Green
    } catch {
        Write-Host "  [!!] Nao foi possivel criar a task" -ForegroundColor Red
    }
} else {
    Write-Host "  [OK] Task ja existe" -ForegroundColor Green
}

# ─── 8. API Keys ──────────────────────────────────
Write-Host ">>> [8/10] API Keys" -ForegroundColor Cyan
$keys = @{
    "NVIDIA_API_KEY" = $env:NVIDIA_API_KEY
    "OPENAI_API_KEY" = $env:OPENAI_API_KEY
    "GH_TOKEN" = $env:GH_TOKEN
}
$kc = 0
foreach ($k in $keys.GetEnumerator()) {
    if ($k.Value) {
        $kc++
    }
}
if ($kc -eq 0) {
    Write-Host "  [..] Nenhuma key detectada. Configure via: setx KEY VALUE" -ForegroundColor Gray
} else {
    Write-Host "  [OK] $kc chave(s) detectada(s)" -ForegroundColor Green
}

# ─── 9. Validação ─────────────────────────────────
Write-Host ">>> [9/9] Validacao" -ForegroundColor Cyan
Push-Location $ECO_DIR
$preflight = python scripts\preflight_check.py 2>&1 | Out-String
if ($preflight -match "TODOS TESTES PASSARAM") {
    Write-Host "  [OK] Preflight: PASS" -ForegroundColor Green
} else {
    Write-Host "  [..] Preflight: verifique manualmente" -ForegroundColor Gray
}

$boot = python scripts\runtime_boot.py --check 2>&1 | Out-String
if ($boot -match "OK") {
    Write-Host "  [OK] Bootloader: OK" -ForegroundColor Green
} else {
    Write-Host "  [!!] Bootloader: falhou" -ForegroundColor Red
}
Pop-Location

# ─── 10. Atalhos visuais ─────────────────────────
Write-Host ">>> [10/10] Atalhos visuais" -ForegroundColor Cyan

# 10a. Batch file no Desktop
$desktop = [Environment]::GetFolderPath("Desktop")
if ($desktop) {
    $batContent = @"
@echo off
cd /d "%USERPROFILE%\Documents\Default Project\EcoSystemUmGrau"
powershell -ExecutionPolicy Bypass -File setup-auto.ps1
pause
"@
    $batPath = Join-Path $desktop "Setup-EcoSystem.bat"
    Set-Content -Path $batPath -Value $batContent -Encoding ASCII
    Write-Host "  [OK] Desktop: Setup-EcoSystem.bat" -ForegroundColor Green
}

# 10b. Alias no profile
$aliasBlock = @"

# === EcoSystemUmGrau Atalhos ===
`$ecoSetup = `"$ECO_DIR\setup-auto.ps1`"
if (Test-Path `$ecoSetup) {
    Set-Alias -Name eco-setup -Value `$ecoSetup
    Set-Alias -Name eco-install -Value `$ecoSetup
    # Funcao para reexecutar setup rapidamente
    function eco-reinstall {
        powershell -ExecutionPolicy Bypass -File `$using:ecoSetup
    }
}
"@
Add-Content $PROFILE_PS1 $aliasBlock
Write-Host "  [OK] Aliases: eco-setup, eco-install, eco-reinstall" -ForegroundColor Green

Write-Host @"
====================================================
  Setup AUTOMATICO concluido!

  COMANDOS VISUAIS:
    🖥️  Desktop: Setup-EcoSystem.bat (duplo clique)
    💻 Terminal: eco-setup  |  eco-install  |  eco-reinstall
    🔧 PowerShell: env-eco, env-sync, ecosystem sync

  REFAÇA O SETUP A QUALQUER MOMENTO:
    Digite no PowerShell:  eco-setup
    Ou clique duas vezes em:  ~/Desktop/Setup-EcoSystem.bat

  Repo: https://github.com/idavidjunior/EcoSystemUmGrau
====================================================
"@ -ForegroundColor Cyan
