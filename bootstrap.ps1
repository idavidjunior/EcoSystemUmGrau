<#
.SYNOPSIS
    Bootstrap do Ecossistema LER + OpenCode + Obsidian em maquina nova.
.DESCRIPTION
    Instala OpenCode, clona o repositorio, configura skills, vault, MCP,
    variaveis de ambiente, chaves de API com validacao, e watcher.
    Um comando, zero config previa.
.PARAMETER VaultPath
    Caminho para o vault Obsidian (default: ~/Desktop/Codigos)
.PARAMETER InstallDir
    Onde clonar o repositorio (default: ~/.local/share/opencode/worktree/mighty-meadow)
.PARAMETER Branch
    Branch do repositorio (default: opencode/mighty-meadow)
.PARAMETER AutoConfigKeys
    Pula a confirmacao e ja pergunta as chaves automaticamente
.EXAMPLE
    powershell -c "iex (iwr -useb https://raw.githubusercontent.com/idavidjunior/EcoSystemUmGrau/opencode/mighty-meadow/bootstrap.ps1)"
#>

param(
    [string]$VaultPath = "$env:USERPROFILE\Desktop\Codigos",
    [string]$InstallDir = "$env:LOCALAPPDATA\opencode\worktree\mighty-meadow",
    [string]$Branch = "opencode/mighty-meadow",
    [switch]$AutoConfigKeys
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Bootstrap Ecossistema LER v2.0"
$RepoUrl = "https://github.com/idavidjunior/EcoSystemUmGrau.git"
$nvidiaOk = $false
$openaiOk = $false

function Step($title) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host ">>> $title" -ForegroundColor White -BackgroundColor DarkBlue
    Write-Host "========================================" -ForegroundColor Cyan
}

function Info($msg) {
    Write-Host "[INFO] $msg" -ForegroundColor Cyan
}

function Ok($msg) {
    Write-Host "[OK] $msg" -ForegroundColor Green
}

function Warn($msg) {
    Write-Host "[AVISO] $msg" -ForegroundColor Yellow
}

function Fail($msg) {
    Write-Host "[FALHA] $msg" -ForegroundColor Red
}

function CheckSuccess($desc) {
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        Fail $desc
        exit 1
    }
    Ok $desc
}

function Read-MaskedInput($prompt) {
    Write-Host "$prompt" -NoNewline -ForegroundColor Yellow
    $plainText = ""
    while ($true) {
        $key = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        if ($key.VirtualKeyCode -eq 13) { break }
        elseif ($key.VirtualKeyCode -eq 8) {
            if ($plainText.Length -gt 0) {
                $plainText = $plainText.Substring(0, $plainText.Length - 1)
                Write-Host "`b `b" -NoNewline
            }
        }
        elseif ($key.Character -ne 0) {
            $plainText += $key.Character
            Write-Host "*" -NoNewline
        }
    }
    Write-Host ""
    return $plainText
}

function Test-ApiKey_Nvidia($key) {
    try {
        $headers = @{ Authorization = "Bearer $key" }
        $result = Invoke-RestMethod -Uri "https://integrate.api.nvidia.com/v1/models" `
            -Headers $headers -Method Get -TimeoutSec 10 -ErrorAction Stop
        if ($result -and $result.models) {
            return $true, "Encontrados $($result.models.Count) modelos disponiveis"
        }
        return $true, "API respondeu (modelos viaveis)"
    } catch {
        $code = [int]$_.Exception.Response.StatusCode
        if ($code -eq 401) { return $false, "Chave invalida (HTTP 401 - Nao autorizado)" }
        if ($code -eq 403) { return $false, "Chave invalida (HTTP 403 - Proibido)" }
        if ($code -eq 429) { return $false, "Rate limit excedido (HTTP 429)" }
        return $false, "Falha na conexao: $_"
    }
}

function Test-ApiKey_OpenAI($key) {
    try {
        $headers = @{ Authorization = "Bearer $key" }
        $result = Invoke-RestMethod -Uri "https://api.openai.com/v1/models" `
            -Headers $headers -Method Get -TimeoutSec 10 -ErrorAction Stop
        if ($result -and $result.data) {
            $gptModels = ($result.data | Where-Object { $_.id -match "gpt" }).Count
            return $true, "Encontrados $gptModels modelos GPT disponiveis"
        }
        return $true, "API respondeu"
    } catch {
        $code = [int]$_.Exception.Response.StatusCode
        if ($code -eq 401) { return $false, "Chave invalida (HTTP 401 - Nao autorizado)" }
        if ($code -eq 429) { return $false, "Quota excedida ou rate limit (HTTP 429)" }
        return $false, "Falha na conexao: $_"
    }
}

function Configure-ApiKey($name, $varName, $testFn) {
    Write-Host ""
    Write-Host "--- $name ---" -ForegroundColor Cyan

    $existing = [Environment]::GetEnvironmentVariable($varName, "User")
    if ($existing) {
        $masked = $existing.Substring(0, [Math]::Min(8, $existing.Length)) + "..."
        Write-Host "Chave existente: $masked" -ForegroundColor Gray

        $choice = Read-Host "Manter chave existente? (S/N)"
        if ($choice -eq "S" -or $choice -eq "s" -or $choice -eq "") {
            Ok "Chave mantida"
            return $true
        }
    }

    $key = Read-MaskedInput "Cole sua chave da $name e pressione Enter: "

    if ([string]::IsNullOrWhiteSpace($key)) {
        Warn "Nenhuma chave fornecida. Pode configurar depois manualmente."
        return $false
    }

    Write-Host "  Testando conexao..." -NoNewline
    $valid, $msg = & $testFn $key

    if ($valid) {
        Write-Host " OK!" -ForegroundColor Green
        Ok "$($name): $msg"
        [Environment]::SetEnvironmentVariable($varName, $key, "User")
        Set-Item -Path "Env:$varName" -Value $key
        Ok "Chave salva em variavel de ambiente (usuario)"
        return $true
    } else {
        Write-Host " FALHOU" -ForegroundColor Red
        Fail "$($name): $msg"
        Warn "Dica: Copie a chave do painel da $name e cole acima."
        return $false
    }
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
        Ok "$($p.Name): $($out -join '')"
    } catch {
        Fail "$($p.Name) - Instale antes de prosseguir"
        Write-Host "    Git: https://git-scm.com/downloads" -ForegroundColor Yellow
        Write-Host "    Node.js: https://nodejs.org/" -ForegroundColor Yellow
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
    Ok "OpenCode ja instalado em $($oc.Source)"
} else {
    Info "Instalando opencode-ai via npm..."
    npm install -g opencode-ai
    CheckSuccess "OpenCode instalado"
}

# ============================================================
# PASSO 3: VAULT_PATH
# ============================================================
Step "3/6 - Configurando VAULT_PATH"

[Environment]::SetEnvironmentVariable("VAULT_PATH", $VaultPath, "User")
Set-Item -Path "Env:VAULT_PATH" -Value $VaultPath
Ok "VAULT_PATH = $VaultPath"

# ============================================================
# PASSO 4: Chaves de API (plug and play)
# ============================================================
Step "4/6 - Chaves de API (plug and play)"

Write-Host ""
Write-Host "Quer configurar as chaves de API agora?" -ForegroundColor White -BackgroundColor DarkBlue
Write-Host ""
Write-Host "O bootstrap vai:" -ForegroundColor Cyan
Write-Host "  1. Pedir para colar sua chave (digitacao mascarada com *)"
Write-Host "  2. Salvar como variavel de ambiente do Windows"
Write-Host "  3. Testar a conexao com a API"
Write-Host "  4. Confirmar se esta funcionando"
Write-Host ""

$configureNow = Read-Host "Configurar chaves agora? (S/N)"
if ($configureNow -eq "S" -or $configureNow -eq "s" -or $configureNow -eq "" -or $AutoConfigKeys) {
    $testNvidia = (Get-Command Test-ApiKey_Nvidia).ScriptBlock
    $testOpenai = (Get-Command Test-ApiKey_OpenAI).ScriptBlock
    $nvidiaOk = Configure-ApiKey "NVIDIA" "NVIDIA_API_KEY" $testNvidia
    $openaiOk = Configure-ApiKey "OpenAI" "OPENAI_API_KEY" $testOpenai

    Write-Host ""
    Write-Host "--- Resumo das chaves ---" -ForegroundColor Cyan
    if ($nvidiaOk) { Ok "NVIDIA_API_KEY: configurada e testada" } else { Warn "NVIDIA_API_KEY: pendente" }
    if ($openaiOk) { Ok "OPENAI_API_KEY: configurada e testada" } else { Warn "OPENAI_API_KEY: pendente" }
} else {
    Warn "Configuracao de chaves pulada."
    Warn "Para configurar manualmente depois:"
    Write-Host '  [Environment]::SetEnvironmentVariable("NVIDIA_API_KEY", "nvapi-...", "User")' -ForegroundColor Gray
    Write-Host '  [Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-proj-...", "User")' -ForegroundColor Gray
}

# ============================================================
# PASSO 5: Clonar repositorio
# ============================================================
Step "5/6 - Clonando repositorio do ecossistema"

if (Test-Path "$InstallDir\.git") {
    Warn "Repo ja existe em $InstallDir. Atualizando..."
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
# PASSO 6: Executar setup completo
# ============================================================
Step "6/6 - Executando setup do ecossistema"

& "$InstallDir\setup.ps1" -VaultPath $VaultPath -InstallDir $InstallDir -SkipClone:$true
CheckSuccess "Setup concluido"

# ============================================================
# VERIFICACAO FINAL
# ============================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ECOSSISTEMA INSTALADO COM SUCESSO!" -ForegroundColor White -BackgroundColor DarkGreen
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Instalado em:     $InstallDir" -ForegroundColor Gray
Write-Host "Vault em:         $VaultPath" -ForegroundColor Gray
Write-Host "Config OpenCode:  $env:USERPROFILE\.config\opencode\opencode.jsonc" -ForegroundColor Gray
Write-Host ""
Write-Host "Comandos para comecar:" -ForegroundColor Cyan
Write-Host "  opencode              Iniciar o OpenCode" -ForegroundColor White
Write-Host "  ler --status          Verificar status do LER" -ForegroundColor White
Write-Host "  ler --audit           Auditar o projeto" -ForegroundColor White

if ($nvidiaOk -or $openaiOk) {
    Write-Host ""
    Write-Host "Chaves de API:" -ForegroundColor Green
    if ($nvidiaOk) { Write-Host "  [OK] NVIDIA_API_KEY configurada e testada" -ForegroundColor Green }
    if ($openaiOk) { Write-Host "  [OK] OPENAI_API_KEY configurada e testada" -ForegroundColor Green }
}