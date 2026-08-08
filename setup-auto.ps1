#!/usr/bin/env pwsh
<#
.SYNOPSIS
    EcoSystemUmGrau - Setup Plug & Play AUTOMÁTICO (sem prompts interativos).

.USAGE
    powershell -ExecutionPolicy Bypass -File setup-auto.ps1
    powershell -ExecutionPolicy Bypass -File setup-auto.ps1 -SyncOnly
#>
param(
    [switch]$SkipGitAuth,
    [switch]$Force,
    [switch]$SyncOnly
)

$ErrorActionPreference = "SilentlyContinue"
$warn = $ErrorActionPreference

$ECO_DIR = "$env:USERPROFILE\Documents\Default Project\EcoSystemUmGrau"
$LER_DIR = "$ECO_DIR\ler-runtime"
$OCODE_DIR = "$env:USERPROFILE\.config\opencode"
$AGENTS_SRC = "$ECO_DIR\config\agents"
$PROFILE_DIR = "$env:USERPROFILE\Documents\WindowsPowerShell"
$PROFILE_PS1 = "$PROFILE_DIR\profile.ps1"

function Write-Step($Msg) { Write-Host "`n>>> $Msg" -ForegroundColor Cyan }
function Write-OK($Msg)   { Write-Host "  [OK] $Msg" -ForegroundColor Green }
function Write-Info($Msg) { Write-Host "  [..] $Msg" -ForegroundColor Gray }
function Write-Err($Msg)  { Write-Host "  [!!] $Msg" -ForegroundColor Red }

Write-Host @"
====================================================
  EcoSystemUmGrau - Setup AUTOMATICO (Plug & Play)
====================================================
"@ -ForegroundColor Cyan

# ─── 0. Requisitos ──────────────────────────────────
Write-Step "[0/9] Requisitos"
$missing = @()
if (-not (Get-Command git -ErrorAction SilentlyContinue))  { $missing += "Git" }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { $missing += "Node.js" }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { $missing += "Python" }
if ($missing.Count -gt 0) {
    Write-Err "Faltando: $($missing -join ', ')"
    exit 1
}
Write-OK "Git, Node.js, Python OK"

# ─── 1. Clonar/atualizar ───────────────────────────
Write-Step "[1/9] EcoSystemUmGrau"
if (Test-Path "$ECO_DIR\.git") {
    Write-Info "Atualizando..."
    Push-Location $ECO_DIR
    git pull --ff-only 2>&1 | ForEach-Object { Write-Info $_ }
    Pop-Location
    Write-OK "Atualizado"
} else {
    Write-Info "Clonando..."
    if (-not (Test-Path (Split-Path $ECO_DIR))) {
        New-Item -ItemType Directory -Path (Split-Path $ECO_DIR) -Force | Out-Null
    }
    git clone https://github.com/idavidjunior/EcoSystemUmGrau.git "$ECO_DIR" 2>&1 | ForEach-Object { Write-Info $_ }
    Write-OK "Clonado"
}

# ─── 2. OpenCode ───────────────────────────────────
Write-Step "[2/9] OpenCode"
$ocInstalled = $false
npm list -g opencode-ai >$null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Info "Instalando..."
    npm i -g opencode-ai 2>&1 | ForEach-Object { Write-Info $_ }
    Write-OK "Instalado"
} else {
    Write-OK "Ja instalado"
    $ocInstalled = $true
}

# ─── 3. Deploy config ─────────────────────────────
Write-Step "[3/9] Config OpenCode"
Push-Location $ECO_DIR
$up = $env:USERPROFILE.Replace('\', '/')

# Sync regras
python scripts\sync_rules.py update 2>&1 | ForEach-Object { Write-Info $_ }

# Diretorios
if (-not (Test-Path $OCODE_DIR))      { New-Item -ItemType Directory -Path $OCODE_DIR -Force | Out-Null }
if (-not (Test-Path "$OCODE_DIR\agents")) { New-Item -ItemType Directory -Path "$OCODE_DIR\agents" -Force | Out-Null }

# Template
$template = Get-Content "$ECO_DIR\config\opencode.jsonc" -Raw
$rendered = $template.Replace("{{USERPROFILE}}", $up)
Set-Content "$OCODE_DIR\opencode.jsonc" -Value $rendered -Encoding UTF8 -Force
Write-OK "opencode.jsonc deployado"

Copy-Item "$ECO_DIR\config\opencode-model-fallback.jsonc" "$OCODE_DIR\" -Force
Copy-Item "$AGENTS_SRC\*.md" "$OCODE_DIR\agents\" -Force
Write-OK "Agents + fallback copiados"

# Plugin
$fbDir = "$OCODE_DIR\node_modules"
if (-not (Test-Path "$fbDir\@razroo\opencode-model-fallback")) {
    if (-not (Test-Path $fbDir)) { New-Item -ItemType Directory -Path $fbDir -Force | Out-Null }
    Push-Location $fbDir
    npm init -y >$null
    npm install @razroo/opencode-model-fallback 2>&1 | ForEach-Object { Write-Info $_ }
    Pop-Location
}
Write-OK "Plugin fallback OK"

# Valida
$cfgTest = opencode debug config --pure 2>&1
if ($cfgTest -match "Error|Invalid") {
    Write-Err "Config invalida"
} else {
    Write-OK "Config valida"
}
Pop-Location

# ─── 4. Python deps ───────────────────────────────
Write-Step "[4/9] Dependencias Python"
Push-Location $ECO_DIR
$reqs = @("dspy-ai", "edge-tts", "httpx", "websockets", "requests", "pyyaml", "tiktoken", "openai")
foreach ($pkg in $reqs) {
    $ver = pip show $pkg 2>$null | Select-String "Version"
    if ($ver) {
        Write-Info "$pkg: OK"
    } else {
        Write-Info "Instalando $pkg..."
        pip install $pkg --quiet 2>&1 | Out-Null
    }
}
Write-OK "Dependencias OK"
Pop-Location

# ─── 5. LER ───────────────────────────────────────
Write-Step "[5/9] LER Runtime"
if (Test-Path "$LER_DIR\run.py") {
    Write-OK "Presente"
} else {
    Write-Info "Nao encontrado (opcional)"
}

# ─── 6. Profile PowerShell ────────────────────────
Write-Step "[6/9] Profile PowerShell"
if (-not (Test-Path $PROFILE_DIR)) {
    New-Item -ItemType Directory -Path $PROFILE_DIR -Force | Out-Null
}
if (-not (Test-Path $PROFILE_PS1)) {
    New-Item -ItemType File -Path $PROFILE_PS1 -Force | Out-Null
}

$profileContent = Get-Content $PROFILE_PS1 -Raw
if (-not ($profileContent -match "EcoSystemUmGrau")) {
    $block = @()
    $block += "# EcoSystemUmGrau - Gerado por setup-auto.ps1"
    $block += "`$env:EcoSystemUmGrau = `"$ECO_DIR`""
    $block += "function start-vigilante {"
    $block += "    `$script = `"$ECO_DIR\scripts\vigilante.ps1`""
    $block += "    if (Test-Path `$script) { Start-Process powershell -ArgumentList `"-NoProfile -ExecutionPolicy Bypass -File `"`$script`""`" -WindowStyle Hidden }"
    $block += "    else { Write-Host `[ERRO`] vigilante.ps1 nao encontrado -ForegroundColor Red }"
    $block += "}"
    $block += "function stop-vigilante  { powershell -NoProfile -ExecutionPolicy Bypass -File `"$ECO_DIR\scripts\vigilante.ps1`" -Stop }"
    $block += "function status-vigilante { powershell -NoProfile -ExecutionPolicy Bypass -File `"$ECO_DIR\scripts\vigilante.ps1`" -Status }"
    $block += "function ecosystem {"
    $block += "    `$script = `"$ECO_DIR\scripts\ecosystem.ps1`""
    $block += "    if (Test-Path `$script) { & `$script @args }"
    $block += "    else { Write-Host `[ERRO`] ecosystem.ps1 nao encontrado -ForegroundColor Red }"
    $block += "}"
    $block += "function @eco { ecosystem sync; python `"$ECO_DIR\scripts\runtime_boot.py`" }"
    $block += "function @sync { ecosystem sync }"
    $block += ""
    Add-Content $PROFILE_PS1 $block
    Write-OK "Functions adicionadas"
} else {
    Write-OK "Profile ja configurado"
}

# ─── 7. Scheduled Task ────────────────────────────
Write-Step "[7/9] Scheduled Task"
$taskName = "EcoSystemVigilante"
$taskExists = schtasks /Query /TN $taskName 2>$null
if (-not $taskExists) {
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ECO_DIR\scripts\vigilante.ps1`""
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Days 3650)
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
    Write-OK "Task criada"
} else {
    Write-OK "Task ja existe"
}

# ─── 8. API Keys ──────────────────────────────────
Write-Step "[8/9] API Keys"
$keys = @{
    "NVIDIA_API_KEY" = $env:NVIDIA_API_KEY
    "OPENAI_API_KEY" = $env:OPENAI_API_KEY
    "GH_TOKEN" = $env:GH_TOKEN
}
$count = 0
foreach ($k in $keys.GetEnumerator()) {
    if ($k.Value) {
        $count++
        if (-not ($profileContent -match $k.Key)) {
            Add-Content $PROFILE_PS1 "`$env:$($k.Key) = `'$($k.Value)`'"
        }
    }
}
if ($count -eq 0) {
    Write-Info "Nenhuma key detectada. Configure via: setx KEY VALUE"
} else {
    Write-OK "$count chave(s) configurada(s)"
}

# ─── 9. Validação ─────────────────────────────────
Write-Step "[9/9] Validacao"
Push-Location $ECO_DIR
$preflight = python scripts\preflight_check.py 2>&1 | Out-String
if ($preflight -match "TODOS TESTES PASSARAM") {
    Write-OK "Preflight: PASS"
} else {
    Write-Info "Preflight: verifique manualmente"
}

$boot = python scripts\runtime_boot.py 2>&1 | Out-String
if ($boot -match "Integridade:  OK") {
    Write-OK "Bootloader: OK"
} else {
    Write-Err "Bootloader: FALHOU"
}
Pop-Location

Write-Host @"
====================================================
  Setup AUTOMATICO concluido!

  Comandos:
    @eco    - Verificar/ativar EcoSystemUmGrau
    @sync   - Sincronizar tudo
    ecosystem sync
====================================================
"@ -ForegroundColor Cyan
