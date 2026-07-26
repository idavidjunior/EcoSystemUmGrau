<#
.SYNOPSIS
    Sincroniza o repositório para o pendrive (backup físico).
    Como o pendrive é lento para git, usa robocopy para snapshot dos arquivos.
    Para usar git em outra máquina: clone do GitHub.

.DESCRIPTION
    Copia todos os arquivos do repo para o pendrive (excluindo builds/caches).
    Escreve um arquivo VERSION.txt com o hash do último commit.
    Adiciona o pendrive como remote no repo principal (opcional).

.PARAMETER Pendrive
    Letra do pendrive (default: E:)
.PARAMETER RepoDir
    Diretório do repositório local
.PARAMETER InstallGitRemote
    Se true, adiciona pendrive como remote git
#>

param(
    [string]$Pendrive = "E:",
    [string]$RepoDir = "",
    [switch]$InstallGitRemote = $false
)

function Write-Log { param([string]$Msg, [string]$Color = "Gray") Write-Host "[PENDRIVE] $Msg" -ForegroundColor $Color }

# Auto-detect repo root
if (-not $RepoDir) {
    $RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$pendriveRepo = "$Pendrive\EcoSystemUmGrau"

# Verificar se pendrive está disponível
if (-not (Test-Path $Pendrive)) {
    Write-Log "Pendrive $Pendrive NAO disponivel" -Color Red
    return $false
}

Write-Log "Sincronizando para $pendriveRepo ..."

# 1. Pegar hash do último commit
$lastCommit = git -C $RepoDir log --oneline -1 2>$null
Write-Log "Ultimo commit: $lastCommit" -Color Cyan

# 2. Robocopy (excluir caches, builds, git)
$excludeDirs = @(
    ".git", "__pycache__", ".pytest_cache", "node_modules",
    ".gradle", ".cxx", "build", "bin", "obj"
)
$excludeArgs = $excludeDirs | ForEach-Object { "/xd", "`"$_`"" }
$excludeFiles = @("*.apk", "*.aab", "*.jar", "*.dex", "*.class", "*.keystore")

$robocopyCmd = "robocopy `"$RepoDir`" `"$pendriveRepo`" /MIR /NDL /NFL /NJH /NJS /R:1 /W:0 /XD .git __pycache__ .pytest_cache node_modules .gradle .cxx build bin obj /XF *.apk *.aab *.jar *.dex *.class *.keystore"
Write-Log "Copiando arquivos..." -Color Cyan
cmd /c $robocopyCmd 2>&1 | Out-Null
Write-Log "Robocopy concluido" -Color Green

# 3. Escrever arquivo de versão
$versionInfo = @"
EcoSystemUmGrau - Snapshot
Data: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Ultimo commit: $lastCommit
Repo: https://github.com/idavidjunior/EcoSystemUmGrau.git
Para clonar com git: git clone https://github.com/idavidjunior/EcoSystemUmGrau.git
"@
Set-Content -Path "$pendriveRepo\VERSION.txt" -Value $versionInfo -Encoding UTF8
Write-Log "VERSION.txt escrito" -Color Green

# 4. Contagem final
$count = (Get-ChildItem $pendriveRepo -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
$size = (Get-ChildItem $pendriveRepo -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
Write-Log "Pendrive atualizado: $count arquivos, $('{0:N2}' -f ($size/1MB)) MB" -Color Green

# 5. Opcional: adicionar como remote git
if ($InstallGitRemote) {
    $remoteName = "pendrive"
    $barePath = "$Pendrive\EcoSystemUmGrau.git"
    if (-not (Test-Path $barePath)) {
        Write-Log "Criando bare repo no pendrive (lento)..." -Color Yellow
        $tmpBare = "$env:TEMP\_pendrive_gitbare"
        Remove-Item -Recurse -Force $tmpBare -ErrorAction SilentlyContinue
        git clone --bare --quiet $RepoDir $tmpBare
        robocopy $tmpBare $barePath /MIR /NDL /NFL /NJH /NJS /R:0 /W:0 | Out-Null
        Remove-Item -Recurse -Force $tmpBare -ErrorAction SilentlyContinue
    }
    git -C $RepoDir remote remove $remoteName -ErrorAction SilentlyContinue
    git -C $RepoDir remote add $remoteName $barePath
    Write-Log "Remote '$remoteName' adicionado" -Color Cyan
}

return $true
