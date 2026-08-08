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

$ECO_DIR = "$env:USERPROFILE\Documents\Default Project\EcoSystemUmGrau"
$OCODE_DIR = "$env:USERPROFILE\.config\opencode"
$AGENTS_SRC = "$ECO_DIR\config\agents"
$PROFILE_DIR = "$env:USERPROFILE\Documents\WindowsPowerShell"
$PROFILE_PS1 = "$PROFILE_DIR\profile.ps1"

function Step($Msg) { Write-Host "`n>>> $Msg" -ForegroundColor Cyan }
function OK($Msg)   { Write-Host "  [OK] $Msg" -ForegroundColor Green }
function Info($Msg) { Write-Host "  [..] $Msg" -ForegroundColor Gray }
function Err($Msg)  { Write-Host "  [!!] $Msg" -ForegroundColor Red }

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  EcoSystemUmGrau - Setup AUTOMATICO (Plug & Play)" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# ─── 0. Requisitos ──────────────────────────────────
Step "[0/9] Requisitos"
$missing = @()
if (-not (Get-Command git -EA SilentlyContinue))  { $missing += "Git" }
if (-not (Get-Command node -EA SilentlyContinue)) { $missing += "Node.js" }
if (-not (Get-Command python -EA SilentlyContinue)) { $missing += "Python" }
if ($missing.Count -gt 0) {
    Err "Faltando: $($missing -join ', ')"
    exit 1
}
OK "Git, Node.js, Python detectados"

# ─── 1. Clonar/atualizar ───────────────────────────
Step "[1/9] EcoSystemUmGrau"
if (Test-Path "$ECO_DIR\.git") {
    Info "Atualizando repo..."
    Push-Location $ECO_DIR
    git pull --ff-only 2>&1 | ForEach-Object { Info $_ }
    Pop-Location
    OK "Repo atualizado"
} else {
    Info "Clonando do GitHub..."
    if (-not (Test-Path (Split-Path $ECO_DIR))) {
        New-Item -ItemType Directory -Path (Split-Path $ECO_DIR) -Force | Out-Null
    }
    git clone https://github.com/idavidjunior/EcoSystemUmGrau.git "$ECO_DIR" 2>&1 | ForEach-Object { Info $_ }
    OK "Clone concluido"
}

# ─── 2. OpenCode ───────────────────────────────────
Step "[2/9] OpenCode"
$null = npm list -g opencode-ai 2>&1
if ($LASTEXITCODE -ne 0) {
    Info "Instalando OpenCode..."
    npm i -g opencode-ai 2>&1 | ForEach-Object { Info $_ }
    OK "OpenCode instalado"
} else {
    OK "OpenCode ja instalado"
}

# ─── 3. Deploy config ─────────────────────────────
Step "[3/9] Config OpenCode"
Push-Location $ECO_DIR
$up = $env:USERPROFILE.Replace('\', '/')

python scripts\sync_rules.py update 2>&1 | ForEach-Object { Info $_ }

if (-not (Test-Path $OCODE_DIR))      { New-Item -ItemType Directory -Path $OCODE_DIR -Force | Out-Null }
if (-not (Test-Path "$OCODE_DIR\agents")) { New-Item -ItemType Directory -Path "$OCODE_DIR\agents" -Force | Out-Null }

$template = Get-Content "$ECO_DIR\config\opencode.jsonc" -Raw
$rendered = $template.Replace("{{USERPROFILE}}", $up)
Set-Content "$OCODE_DIR\opencode.jsonc" -Value $rendered -Encoding UTF8 -Force
OK "opencode.jsonc rendered"

Copy-Item "$ECO_DIR\config\opencode-model-fallback.jsonc" "$OCODE_DIR\" -Force
Copy-Item "$AGENTS_SRC\*.md" "$OCODE_DIR\agents\" -Force
OK "Agents + fallback deployados"

$fbDir = "$OCODE_DIR\node_modules"
if (-not (Test-Path "$fbDir\@razroo\opencode-model-fallback")) {
    if (-not (Test-Path $fbDir)) { New-Item -ItemType Directory -Path $fbDir -Force | Out-Null }
    Push-Location $fbDir
    npm init -y >$null
    npm install @razroo/opencode-model-fallback 2>&1 | ForEach-Object { Info $_ }
    Pop-Location
}
OK "Plugin fallback"

$cfgTest = opencode debug config --pure 2>&1
if ($cfgTest -match "Error|Invalid") {
    Err "Config invalida"
} else {
    OK "Config valida"
}
Pop-Location

# ─── 4. Python deps ───────────────────────────────
Step "[4/9] Python deps"
Push-Location $ECO_DIR
$reqs = @("dspy-ai", "edge-tts", "httpx", "websockets", "requests", "pyyaml", "tiktoken", "openai")
foreach ($pkg in $reqs) {
    $ver = pip show $pkg 2>$null | Select-String "Version"
    $pkgName = $pkg
    if ($ver) {
        Info "$pkgName: OK"
    } else {
        Info "Instalando $pkgName..."
        pip install $pkg --quiet 2>&1 | Out-Null
    }
}
OK "Python deps instaladas"
Pop-Location

# ─── 5. LER ───────────────────────────────────────
Step "[5/9] LER Runtime"
$lerDir = "$ECO_DIR\ler-runtime"
if (Test-Path "$lerDir\run.py") {
    OK "LER runtime presente"
} else {
    Info "LER runtime nao encontrado (opcional)"
}

# ─── 6. Profile PowerShell ────────────────────────
Step "[6/9] Profile PowerShell"
if (-not (Test-Path $PROFILE_DIR)) {
    New-Item -ItemType Directory -Path $PROFILE_DIR -Force | Out-Null
}
if (-not (Test-Path $PROFILE_PS1)) {
    New-Item -ItemType File -Path $PROFILE_PS1 -Force | Out-Null
}

$pc = Get-Content $PROFILE_PS1 -Raw
if (-not ($pc -match "EcoSystemUmGrau")) {
    # Template approach: generate from a separate file to avoid escaping issues
    $profileBlock = @()
    $profileBlock += "# EcoSystemUmGrau - Generated by setup-auto.ps1"
    $profileBlock += "`$env:EcoSystemUmGrau = `"$ECO_DIR`""
    $profileBlock += "function start-vigilante {"
    $profileBlock += "    `$s = join-path `$env:EcoSystemUmGrau 'scripts\vigilante.ps1'"
    $profileBlock += "    if (Test-Path `$s) { Start-Process powershell -ArgumentList `"-NoProfile -ExecutionPolicy Bypass -File" + "`"$s`""`" -WindowStyle Hidden }"
    $profileBlock += "    else { Write-Host '[ERRO] vigilante.ps1 nao encontrado' -ForegroundColor Red }"
    $profileBlock += "}"
    $profileBlock += "function stop-vigilante  { powershell -NoProfile -ExecutionPolicy Bypass -File (join-path `$env:EcoSystemUmGrau 'scripts\vigilante.ps1') -Stop }"
    $profileBlock += "function status-vigilante { powershell -NoProfile -ExecutionPolicy Bypass -File (join-path `$env:EcoSystemUmGrau 'scripts\vigilante.ps1') -Status }"
    $profileBlock += "function ecosystem {"
    $profileBlock += "    `$s = join-path `$env:EcoSystemUmGrau 'scripts\ecosystem.ps1'"
    $profileBlock += "    if (Test-Path `$s) { & `$s @args }"
    $profileBlock += "    else { Write-Host '[ERRO] ecosystem.ps1 nao encontrado' -ForegroundColor Red }"
    $profileBlock += "}"
    $profileBlock += "function otimizar { python (join-path `$env:EcoSystemUmGrau 'scripts\prompt_optimizer_cli.py') @args }"
    $profileBlock += "function env-eco { ecosystem sync; python (join-path `$env:EcoSystemUmGrau 'scripts\runtime_boot.py') }"
    $profileBlock += "function env-sync { ecosystem sync }"
    $profileBlock += ""
    Add-Content $PROFILE_PS1 ($profileBlock -join "`n")
    OK "Profile functions added (use: env-eco, env-sync)"
} else {
    OK "Profile ja configurado"
}

# ─── 7. Scheduled Task ────────────────────────────
Step "[7/9] Scheduled Task"
$tn = "EcoSystemVigilante"
$te = schtasks /Query /TN $tn 2>$null
if (-not $te) {
    try {
        $a = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ECO_DIR\scripts\vigilante.ps1`""
        $t = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
        $s = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Days 3650)
        Register-ScheduledTask -TaskName $tn -Action $a -Trigger $t -Settings $s -Force | Out-Null
        OK "Task criada"
    } catch {
        Err "Nao foi possivel criar a task: $_"
    }
} else {
    OK "Task ja existe"
}

# ─── 8. API Keys ──────────────────────────────────
Step "[8/9] API Keys"
$keys = @{
    "NVIDIA_API_KEY" = $env:NVIDIA_API_KEY
    "OPENAI_API_KEY" = $env:OPENAI_API_KEY
    "GH_TOKEN" = $env:GH_TOKEN
}
$kc = 0
foreach ($k in $keys.GetEnumerator()) {
    if ($k.Value) {
        $kc++
        if (-not ($pc -match $k.Key)) {
            Add-Content $PROFILE_PS1 "`$env:$($k.Key) = `'$($k.Value)`'"
        }
    }
}
if ($kc -eq 0) {
    Info "Nenhuma key detectada. Configure via: setx KEY VALUE"
} else {
    OK "$kc chave(s) configurada(s)"
}

# ─── 9. Validação ─────────────────────────────────
Step "[9/9] Validacao"
Push-Location $ECO_DIR
$preflight = python scripts\preflight_check.py 2>&1 | Out-String
if ($preflight -match "TODOS TESTES PASSARAM") {
    OK "Preflight: PASS"
} else {
    Info "Preflight: verifique manualmente"
}

$boot = python scripts\runtime_boot.py --check 2>&1 | Out-String
if ($boot -match "OK") {
    OK "Bootloader: OK"
} else {
    Err "Bootloader: falhou"
}
Pop-Location

Write-Host @"
====================================================
  Setup AUTOMATICO concluido!

  Comandos:
    env-eco    - Verificar/ativar EcoSystemUmGrau
    env-sync   - Sincronizar tudo
    ecosystem sync

  Repo: https://github.com/idavidjunior/EcoSystemUmGrau
====================================================
"@ -ForegroundColor Cyan
