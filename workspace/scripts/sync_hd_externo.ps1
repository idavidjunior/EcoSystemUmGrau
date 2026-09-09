<#
.SYNOPSIS
    Espelha o EcoSystemUmGrau para HD externo (E:\Default Project\EcoSystemUmGrau)
.DESCRIPTION
    Usa robocopy para mirror eficiente (apenas deltas). Mantém estrutura idêntica.
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
    Add-Content -Path $logFile -Value $line -Encoding UTF8
    Write-Host $line
}

# Verifica se HD externo está montado
if (-not (Test-Path $Target -PathType Container)) {
    # Tenta criar a pasta raiz se não existir
    try {
        New-Item -ItemType Directory -Path $Target -Force | Out-Null
        Write-Log "Pasta alvo criada: $Target"
    } catch {
        Write-Log "HD externo não acessível em $Target. Pulando sync." "WARN"
        exit 0
    }
}

# Exclusões padrão para mirror
$exclusions = @(
    ".git",
    "node_modules",
    "__pycache__",
    "*.pyc",
    ".venv",
    "venv",
    ".env",
    "*.log",
    "*.bak",
    "*.tmp",
    "build",
    "dist",
    "out",
    "bin",
    "obj",
    ".vs",
    ".vscode",
    "*.swp",
    "*.swo",
    "*~",
    "Thumbs.db",
    "ehthumbs.db",
    "Desktop.ini",
    "conhecimento\evolution-radar\bruto",
    "conhecimento\evolution-radar\filtrado",
    "runtime\backups",
    "runtime\traces",
    ".deer-flow"
)

$excludeArgs = $exclusions | ForEach-Object { "/XD $_" } + ($exclusions | Where-Object { $_ -like "*.*" } | ForEach-Object { "/XF $_" })

# Robocopy flags para mirror
$flags = @(
    "/MIR",
    "/R:2",
    "/W:5",
    "/MT:8",
    "/COPY:DAT",
    "/DCOPY:T",
    "/NP",
    "/NFL",
    "/NDL",
    "/TEE"
)

if ($DryRun) { $flags += "/L" }

Write-Log "Iniciando sync HD externo: $Source -> $Target"
if ($DryRun) { Write-Log "MODO DRY-RUN (apenas lista)" }

$robocopyArgs = @($Source, $Target) + $flags + $excludeArgs
if ($Verbose) { $robocopyArgs += "/V" }

$exitCode = & robocopy.exe @robocopyArgs

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