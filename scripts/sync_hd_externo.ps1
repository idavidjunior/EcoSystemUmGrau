<#
.SYNOPSIS
    Espelha o EcoSystemUmGrau para HD externo (E:\Default Project\EcoSystemUmGrau)
.DESCRIPTION
    Usa robocopy via PowerShell call operator (funciona com paths com espaços).
    Mirror eficiente (apenas deltas). Mantém estrutura idêntica.
    Exclui: .git, node_modules, __pycache__, .venv, logs, builds, artifacts.
.NOTES
    Roda via vigilante timer (configurável). Só executa se HD estiver montado.
#>

param(
    [string]$Source = "C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau",
    [string]$Target = "E:\Default Project\EcoSystemUmGrau",
    [switch]$DryRun,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"

function Write-Log {
    param($Msg, $Level = "INFO")
    $line = "[$(Get-Date -Format 'HH:mm:ss')] [$Level] $Msg"
    $logFile = "$env:USERPROFILE\.sync_hd_externo.log"
    # Garante que o diretório existe
    $logDir = Split-Path $logFile -Parent
    if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    Add-Content -Path $logFile -Value $line -Encoding UTF8
    Write-Host $line
}

# Verifica se HD externo está montado
if (-not (Test-Path $Target -PathType Container)) {
    try {
        New-Item -ItemType Directory -Path $Target -Force | Out-Null
        Write-Log "Pasta alvo criada: $Target"
    } catch {
        Write-Log "HD externo não acessível em $Target. Pulando sync." "WARN"
        exit 0
    }
}

# Diretórios a excluir (apenas nomes, sem caminho)
$excludeDirs = @(
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".git",
    ".vs",
    ".vscode",
    "build",
    "dist",
    "out",
    "bin",
    "obj",
    ".deer-flow"
)

# Arquivos a excluir (padrões)
$excludeFiles = @(
    "*.log",
    "*.bak",
    "*.tmp",
    "*.pyc",
    "*.swp",
    "*.swo",
    "*~",
    "Thumbs.db",
    "ehthumbs.db",
    "Desktop.ini"
)

# Constrói argumentos /XD e /XF para robocopy
$xdArgs = ($excludeDirs | ForEach-Object { "/XD $_" }) -join " "
$xfArgs = ($excludeFiles | ForEach-Object { "/XF $_" }) -join " "

# Constrói comando robocopy via PowerShell call operator (funciona com paths com espaços)
$cmd = "& robocopy '$Source' '$Target' *.* /MIR /R:2 /W:5 /MT:8 /COPY:DAT /DCOPY:T /NP /NFL /NDL /TEE $xdArgs $xfArgs"
if ($DryRun) { $cmd += " /L" }
if ($Verbose) { $cmd += " /V" }

Write-Log "Iniciando sync HD externo: $Source -> $Target"
if ($DryRun) { Write-Log "MODO DRY-RUN (apenas lista)" }
Write-Log "DEBUG: $cmd"

$exitCode = powershell -NoProfile -ExecutionPolicy Bypass -Command $cmd

$success = $exitCode -le 3

if ($success) {
    $msg = if ($exitCode -eq 0) { "Nenhuma mudança (já sincronizado)" }
           elseif ($exitCode -eq 1) { "Arquivos copiados/atualizados" }
           elseif ($exitCode -eq 2) { "Arquivos extras removidos no destino" }
           else { "Sync concluído com mudanças mistas" }
    Write-Log "Sync HD externo OK: $msg (exit code: $exitCode)"
} else {
    Write-Log "Sync HD externo FALHOU (exit code: $exitCode)" "ERROR"
}

if ($success) {
    $marker = "$env:USERPROFILE\.last_hd_sync.txt"
    Set-Content -Path $marker -Value (Get-Date).ToString('o') -Encoding UTF8
}

exit $exitCode