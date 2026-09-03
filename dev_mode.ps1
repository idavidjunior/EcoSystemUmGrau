#requires -version 5.1
#requires -RunAsAdministrator

<#
=======================================================================
 ECO-SYSTEM DEV MODE v2.0
 Windows 10 Development & Automation Environment
=======================================================================

 OBJETIVO
 --------
 Preparar o Windows 10 para ambientes de desenvolvimento e automacao,
 reduzindo bloqueios administrativos sem desativar completamente
 os mecanismos de seguranca do Windows.

 RECURSOS
 --------
 [1]  Criar workspace de desenvolvimento
 [2]  Configurar Execution Policy
 [3]  Adicionar diretorios ao PATH (automatico)
 [4]  Detectar e catalogar ferramentas
 [5]  Conceder controle ao usuario nas pastas do workspace
 [6]  Criar diretorio de logs
 [7]  Criar tarefa administrativa para aplicativos
 [8]  Atualizar ambiente da sessao atual
 [9]  Diagnostico completo do ambiente
 [10] Aplicar configuracao completa
 [11] Restaurar alteracoes principais
 [12] Verificar integridade das operacoes

 IMPORTANTE
 ----------
 - NAO desativa o UAC globalmente.
 - NAO concede privilegios SYSTEM indiscriminadamente.
 - NAO altera TrustedInstaller.
 - NAO abre firewall globalmente.
 - NAO concede controle total ao usuario sobre C:\Windows.
 - Atua principalmente sobre o ambiente de desenvolvimento.
 - Atualiza o PATH na sessao atual sem reiniciar.
=======================================================================
#>

$ErrorActionPreference = "Continue"

# =====================================================================
# CONFIGURACAO
# =====================================================================

$DevRoot = "C:\Dev"
$Workspace = "$DevRoot\Workspace"
$Tools = "$DevRoot\Tools"
$ScriptsDir = "$DevRoot\Scripts"
$Logs = "$DevRoot\Logs"
$TempDir = "$DevRoot\Temp"

$UserName = $env:USERNAME

$ManagedPaths = @(
    $DevRoot,
    $Workspace,
    $Tools,
    $ScriptsDir,
    $Logs,
    $TempDir
)

$LogFile = "$Logs\devmode.log"

$ToolCandidates = @{
    "Python"    = @("python.exe","python3.exe")
    "Node.js"   = @("node.exe")
    "Git"       = @("git.exe")
    "ADB"       = @("adb.exe")
    "Java"      = @("java.exe")
    "Javac"     = @("javac.exe")
    "pip"       = @("pip.exe","pip3.exe")
    "curl"      = @("curl.exe")
}

# =====================================================================
# FUNCOES BASICAS
# =====================================================================

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host " $Text" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-OK {
    param([string]$Text)
    Write-Host "[OK]  $Text" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Text)
    Write-Host "[!]  $Text" -ForegroundColor Yellow
}

function Write-Fail {
    param([string]$Text)
    Write-Host "[ERRO] $Text" -ForegroundColor Red
}

function Write-Info {
    param([string]$Text)
    Write-Host "     $Text" -ForegroundColor White
}

function Log-Message {
    param([string]$Text)
    if (!(Test-Path $Logs)) {
        New-Item -Path $Logs -ItemType Directory -Force | Out-Null
    }
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "$Timestamp - $Text"
    Add-Content -Path $LogFile -Value $LogEntry -ErrorAction SilentlyContinue
}

function Pause-DevMode {
    Write-Host ""
    Read-Host "Pressione ENTER para continuar"
}

# =====================================================================
# ATUALIZAR AMBIENTE DA SESSAO
# =====================================================================

function Update-SessionEnvironment {

    Write-Header "ATUALIZANDO AMBIENTE DA SESSAO"

    $NewPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $CurrentPath = $env:Path

    if ($CurrentPath -notmatch [regex]::Escape($NewPath)) {
        $env:Path = $NewPath
        Write-OK "PATH atualizado na sessao atual"
        Log-Message "PATH atualizado na sessao"
    }
    else {
        Write-OK "PATH ja contem os novos caminhos"
    }

    $env:DevRoot = $DevRoot
    $env:Workspace = $Workspace
    $env:Tools = $Tools

    Write-Info "Para efeito completo, reinicie programas abertos."
}

# =====================================================================
# CRIAR ESTRUTURA
# =====================================================================

function Initialize-DevDirectories {

    Write-Header "CRIANDO ESTRUTURA DE DESENVOLVIMENTO"

    $Created = 0
    $Existed = 0

    foreach ($Path in $ManagedPaths) {

        if (!(Test-Path $Path)) {

            try {

                New-Item -Path $Path -ItemType Directory -Force | Out-Null
                Write-OK "Criado: $Path"
                Log-Message "Diretorio criado: $Path"
                $Created++
            }
            catch {

                Write-Fail "Falha ao criar: $Path"
                Write-Info $_.Exception.Message
                Log-Message "Falha ao criar diretorio: $Path - $($_.Exception.Message)"
            }
        }
        else {

            Write-OK "Ja existe: $Path"
            $Existed++
        }
    }

    $SubDirectories = @(
        "$Workspace\Projects",
        "$Workspace\Git",
        "$Workspace\Python",
        "$Workspace\Android",
        "$Workspace\Jarvis",
        "$Workspace\EcoSystemUmGrau",
        "$Tools\ADB",
        "$Tools\Bin",
        "$ScriptsDir\Startup",
        "$ScriptsDir\Maintenance"
    )

    foreach ($Path in $SubDirectories) {

        if (!(Test-Path $Path)) {

            try {

                New-Item -Path $Path -ItemType Directory -Force | Out-Null
                Write-OK "Criado: $Path"
                Log-Message "Subdiretorio criado: $Path"
                $Created++
            }
            catch {

                Write-Fail "Falha ao criar: $Path"
                Log-Message "Falha ao criar subdiretorio: $Path"
            }
        }
    }

    Write-Host ""
    Write-Info "Resumo: $Created criado(s), $Existed ja existia(m)."
    Log-Message "Estrutura criada: $Created novo(s), $Existed existente(s)"
}

# =====================================================================
# PERMISSOES
# =====================================================================

function Set-DevPermissions {

    Write-Header "CONFIGURANDO PERMISSOES DO WORKSPACE"

    $Success = 0
    $Failed = 0

    foreach ($Path in $ManagedPaths) {

        if (!(Test-Path $Path)) {
            continue
        }

        Write-Host "Configurando: $Path"

        try {

            icacls.exe $Path "/grant ${UserName}:(OI)(CI)M" /T /C | Out-Null

            if ($LASTEXITCODE -eq 0) {
                Write-OK "Permissao Modify concedida: $Path"
                Log-Message "Permissao concedida: $Path"
                $Success++
            }
            else {
                Write-Warn "icacls retornou codigo $LASTEXITCODE para: $Path"
                Log-Message "icacls falhou para $Path (codigo $LASTEXITCODE)"
                $Failed++
            }
        }
        catch {

            Write-Fail "Nao foi possivel configurar: $Path"
            Log-Message "Erro ao configurar permissao: $Path - $($_.Exception.Message)"
            $Failed++
        }
    }

    Write-Host ""
    Write-Info "Permissoes: $Success OK, $Failed falha(s)."
}

# =====================================================================
# EXECUTION POLICY
# =====================================================================

function Configure-PowerShell {

    Write-Header "CONFIGURANDO POWERSHELL"

    try {

        $CurrentPolicy = Get-ExecutionPolicy -Scope CurrentUser
        Write-Info "ExecutionPolicy atual (CurrentUser): $CurrentPolicy"

        Set-ExecutionPolicy `
            -Scope CurrentUser `
            -ExecutionPolicy RemoteSigned `
            -Force

        $NewPolicy = Get-ExecutionPolicy -Scope CurrentUser
        Write-OK "ExecutionPolicy alterada: $CurrentPolicy -> $NewPolicy"
        Log-Message "ExecutionPolicy alterada para RemoteSigned"
    }
    catch {

        Write-Warn "Nao foi possivel alterar ExecutionPolicy."
        Write-Info $_.Exception.Message
        Log-Message "Falha ao alterar ExecutionPolicy: $($_.Exception.Message)"
    }
}

# =====================================================================
# PATH - DETECÇÃO AUTOMATICA E ADIÇÃO
# =====================================================================

function Find-ToolPath {
    param([string[]]$Candidates)

    foreach ($Candidate in $Candidates) {

        $Found = Get-Command $Candidate -ErrorAction SilentlyContinue

        if ($Found) {

            $ToolPath = Split-Path $Found.Source -Parent

            if (Test-Path $ToolPath) {
                return $ToolPath
            }
        }
    }

    return $null
}

function Add-ToUserPath {
    param([string]$Path)

    if (!(Test-Path $Path)) {
        return $false
    }

    $CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $Entries = $CurrentPath -split ";"

    if ($Entries -notcontains $Path) {

        $NewPath = (
            ($Entries + $Path) |
            Where-Object { $_ -and $_.Trim() -ne "" } |
            Select-Object -Unique
        ) -join ";"

        try {
            [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
            Write-OK "PATH += $Path"
            Log-Message "PATH adicionado: $Path"
            return $true
        }
        catch {
            Write-Warn "Nao foi possivel adicionar ao PATH: $Path"
            return $false
        }
    }
    else {
        Write-Info "PATH ja contem: $Path"
        return $true
    }
}

function Configure-Path {

    Write-Header "CONFIGURANDO PATH"

    $Added = 0

    foreach ($PathDir in @($Tools, $ScriptsDir)) {
        if (Add-ToUserPath $PathDir) { $Added++ }
    }

    Write-Host ""
    Write-Info "=== Detectando ferramentas instaladas ==="
    Write-Host ""

    foreach ($ToolName in $ToolCandidates.Keys) {
        $Candidates = $ToolCandidates[$ToolName]
        $ToolPath = Find-ToolPath $Candidates

        if ($ToolPath) {
            Write-OK "$ToolName encontrado: $ToolPath"

            if (Add-ToUserPath $ToolPath) {
                $Added++
            }
        }
        else {
            Write-Warn "$ToolName nao encontrado"
            Log-Message "$ToolName nao encontrado no sistema"
        }
    }

    Write-Host ""
    Write-Info "Caminhos adicionados ao PATH: $Added"
    Write-Host ""
    Write-Info "Novo PATH do usuario:"
    Write-Info ([Environment]::GetEnvironmentVariable("Path", "User"))
    Log-Message "PATH configurado. $Added caminhos adicionados."
}

# =====================================================================
# DETECÇÃO DE FERRAMENTAS
# =====================================================================

function Detect-Tool {
    param([string]$ToolName, [string[]]$Candidates)

    $Result = @{
        Name = $ToolName
        Found = $false
        Path = $null
        Version = $null
    }

    foreach ($Candidate in $Candidates) {
        $Cmd = Get-Command $Candidate -ErrorAction SilentlyContinue

        if ($Cmd) {
            $Result.Found = $true
            $Result.Path = $Cmd.Source

            try {
                switch ($ToolName) {
                    "Python"  { $Result.Version = & $Cmd.Source --version 2>&1 }
                    "Node.js" { $Result.Version = & $Cmd.Source --version 2>&1 }
                    "Git"     { $Result.Version = & $Cmd.Source --version 2>&1 }
                    "ADB"     { $Result.Version = & $Cmd.Source version 2>&1 }
                    "Java"    { $Result.Version = & $Cmd.Source -version 2>&1 }
                    "Javac"   { $Result.Version = & $Cmd.Source -version 2>&1 }
                    "pip"     { $Result.Version = & $Cmd.Source --version 2>&1 }
                    "curl"    { $Result.Version = & $Cmd.Source --version 2>&1 }
                    default   { $Result.Version = "OK" }
                }
            }
            catch {
                $Result.Version = "Desconhecido"
            }

            break
        }
    }

    return $Result
}

function Detect-AllTools {

    Write-Header "DETECENDO FERRAMENTAS INSTALADAS"

    $Detected = @()
    $Missing = @()

    foreach ($ToolName in $ToolCandidates.Keys) {
        $Candidates = $ToolCandidates[$ToolName]
        $Result = Detect-Tool $ToolName $Candidates

        if ($Result.Found) {
            Write-OK "$($Result.Name): $($Result.Path) | $($Result.Version)"
            $Detected += $Result
        }
        else {
            Write-Warn "$($Result.Name): nao encontrado"
            $Missing += $Result
        }
    }

    Write-Host ""
    Write-Info "Total: $($Detected.Count) detectada(s), $($Missing.Count) nao encontrada(s)."
    Log-Message "Ferramentas detectadas: $($Detected.Count), faltando: $($Missing.Count)"

    return @{ Detected = $Detected; Missing = $Missing }
}

# =====================================================================
# LOGS
# =====================================================================

function Initialize-Logs {

    Write-Header "CONFIGURANDO LOGS"

    if (!(Test-Path $Logs)) {
        New-Item -Path $Logs -ItemType Directory -Force | Out-Null
    }

    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "$Timestamp - DEV MODE v2.0 iniciado."

    Write-OK "Log: $LogFile"
    Log-Message "Diretorio de logs inicializado"
}

# =====================================================================
# TAREFA ADMINISTRATIVA - LAUNCHER ELEVADO
# =====================================================================

function Create-ElevatedLauncher {

    Write-Header "CRIANDO GERENCIADOR DE APLICACOES ELEVADAS"

    $LauncherDir = "$ScriptsDir\AdminLauncher"

    if (!(Test-Path $LauncherDir)) {
        New-Item -Path $LauncherDir -ItemType Directory -Force | Out-Null
    }

    $Launcher = "$LauncherDir\Launch-Elevated.ps1"

    $LauncherCode = @'
param(
    [Parameter(Mandatory=$true)]
    [string]$Application,

    [string]$Arguments = ""
)

if (!(Test-Path $Application)) {
    Write-Host "Aplicativo nao encontrado:" -ForegroundColor Red
    Write-Host "  $Application"
    exit 1
}

try {
    if ($Arguments) {
        Start-Process -FilePath $Application -ArgumentList $Arguments -Verb RunAs -Wait
    } else {
        Start-Process -FilePath $Application -Verb RunAs -Wait
    }
    Write-Host "Aplicativo executado com sucesso." -ForegroundColor Green
}
catch {
    Write-Host "Erro ao executar:" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)"
    exit 1
}
'@

    try {
        Set-Content -Path $Launcher -Value $LauncherCode -Encoding UTF8
        Write-OK "Launcher criado: $Launcher"
        Log-Message "Launcher criado: $Launcher"
    }
    catch {
        Write-Warn "Nao foi possivel criar o launcher."
        Log-Message "Falha ao criar launcher: $($_.Exception.Message)"
    }

    $BatLauncher = "$LauncherDir\launch.bat"
    $BatContent = "@echo off`npowershell.exe -ExecutionPolicy Bypass -File `"%~dp0Launch-Elevated.ps1`" %%*"
    try {
        Set-Content -Path $BatLauncher -Value $BatContent -Encoding ASCII
        Write-OK "Atalho batch criado: $BatLauncher"
    }
    catch {
        Write-Warn "Nao foi possivel criar o atalho batch."
    }
}

# =====================================================================
# DIAGNOSTICO
# =====================================================================

function Run-Diagnostics {

    Write-Header "DIAGNOSTICO DO AMBIENTE"

    Write-Host ""
    Write-Info "=== Sistema Operacional ==="
    try {
        Get-CimInstance Win32_OperatingSystem |
            Select-Object Caption, Version, BuildNumber, OSArchitecture |
            Format-List
    }
    catch { Write-Warn "Nao foi possivel obter informacoes do SO" }

    Write-Host ""
    Write-Info "=== Usuario ==="
    Write-Host "Nome: $UserName"
    Write-Host "Dominio: $($env:USERDOMAIN)"

    Write-Host ""
    Write-Info "=== PowerShell ==="
    Write-Host "Versao: $($PSVersionTable.PSVersion)"
    Write-Host "Host: $($Host.Name)"

    Write-Host ""
    Write-Info "=== Execution Policy ==="
    Get-ExecutionPolicy -List | Format-Table -AutoSize

    Write-Host ""
    Write-Info "=== PATH do Usuario ==="
    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $UserPath -split ";" | ForEach-Object { Write-Host "  $_" }

    Write-Host ""
    Write-Info "=== PATH da Maquina ==="
    $MachinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $MachinePath -split ";" | ForEach-Object { Write-Host "  $_" }

    Write-Host ""
    Write-Info "=== Variaveis de Ambiente ==="
    Write-Host "DevRoot:    $DevRoot"
    Write-Host "Workspace:  $Workspace"
    Write-Host "Tools:      $Tools"
    Write-Host "ScriptsDir: $ScriptsDir"
    Write-Host "Logs:       $Logs"
    Write-Host "TempDir:    $TempDir"

    Write-Host ""
    Detect-AllTools
}

# =====================================================================
# VERIFICAR INTEGRIDADE
# =====================================================================

function Test-DevModeIntegrity {

    Write-Header "VERIFICANDO INTEGRIDADE DO DEV MODE"

    $Checks = @()

    foreach ($Path in $ManagedPaths) {
        $Exists = Test-Path $Path
        $Checks += @{
            Item = "Diretorio: $Path"
            Status = if ($Exists) { "OK" } else { "FALTA" }
        }
    }

    foreach ($ToolName in $ToolCandidates.Keys) {
        $Candidates = $ToolCandidates[$ToolName]
        $Found = $false
        foreach ($Candidate in $Candidates) {
            if (Get-Command $Candidate -ErrorAction SilentlyContinue) {
                $Found = $true
                break
            }
        }
        $Checks += @{
            Item = "Ferramenta: $ToolName"
            Status = if ($Found) { "OK" } else { "FALTA" }
        }
    }

    $Policy = Get-ExecutionPolicy -Scope CurrentUser
    $Checks += @{
        Item = "ExecutionPolicy (CurrentUser)"
        Status = if ($Policy -eq "RemoteSigned") { "OK" } else { "=$Policy" }
    }

    $Launcher = "$ScriptsDir\AdminLauncher\Launch-Elevated.ps1"
    $Checks += @{
        Item = "Launcher elevado"
        Status = if (Test-Path $Launcher) { "OK" } else { "FALTA" }
    }

    $Checks += @{
        Item = "Arquivo de log"
        Status = if (Test-Path $LogFile) { "OK" } else { "FALTA" }
    }

    $AllOK = $true
    foreach ($Check in $Checks) {
        if ($Check.Status -eq "OK") {
            Write-OK "$($Check.Item): $($Check.Status)"
        }
        elseif ($Check.Status -eq "FALTA") {
            Write-Fail "$($Check.Item): $($Check.Status)"
            $AllOK = $false
        }
        else {
            Write-Warn "$($Check.Item): $($Check.Status)"
            $AllOK = $false
        }
    }

    Write-Host ""
    if ($AllOK) {
        Write-OK "Todos os verificacoes passaram!"
    }
    else {
        Write-Warn "Algumas verificacoes precisam de atencao."
    }

    return $AllOK
}

# =====================================================================
# APLICAR CONFIGURACAO COMPLETA
# =====================================================================

function Apply-DevMode {

    Write-Header "APLICANDO DEV MODE COMPLETO v2.0"

    Log-Message "=== DEV MODE v2.0 - Aplicacao completa iniciada ==="

    Initialize-DevDirectories
    Configure-PowerShell
    Configure-Path
    Set-DevPermissions
    Initialize-Logs
    Create-ElevatedLauncher
    Update-SessionEnvironment

    Write-Host ""
    Write-Header "DEV MODE CONCLUIDO"

    Write-OK "Ambiente preparado com sucesso."
    Write-Host ""
    Write-Host "Diretorio raiz:"
    Write-Host "  $DevRoot"
    Write-Host ""
    Write-Host "Workspace:"
    Write-Host "  $Workspace"
    Write-Host ""
    Write-Host "Ferramentas adicionadas ao PATH na sessao atual."
    Write-Host "Para efeito completo em programas ja abertos,"
    Write-Host "reinicie-os ou execute Update-SessionEnvironment."

    Log-Message "=== DEV MODE v2.0 - Aplicacao completa concluida ==="
}

# =====================================================================
# RESTAURAR CONFIGURACOES
# =====================================================================

function Restore-DevMode {

    Write-Header "RESTAURAR CONFIGURACOES DO DEV MODE"

    Write-Host "Esta operacao remove SOMENTE as configuracoes criadas"
    Write-Host "por este script, preservando seus projetos."
    Write-Host ""

    Write-Host "O que sera feito:"
    Write-Host "  - Remover entradas do PATH adicionadas pelo script"
    Write-Host "  - Remover ExecutionPolicy configurado (reseta para Undefined)"
    Write-Host "  - Remover o launcher administrativo"
    Write-Host "  - REMOVER as pastas de desenvolvimento (C:\Dev)"
    Write-Host ""

    $Confirm = Read-Host "Digite RESTAURAR para confirmar"

    if ($Confirm -ne "RESTAURAR") {
        Write-Warn "Operacao cancelada."
        Log-Message "Restauracao cancelada pelo usuario"
        return
    }

    # Restaurar Execution Policy
    try {
        Set-ExecutionPolicy `
            -Scope CurrentUser `
            -ExecutionPolicy Undefined `
            -Force
        Write-OK "ExecutionPolicy restaurada para Undefined."
        Log-Message "ExecutionPolicy restaurada."
    }
    catch {
        Write-Warn "Nao foi possivel restaurar ExecutionPolicy."
    }

    # Remover entradas do PATH
    try {
        $CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")
        $PathsToRemove = @($DevRoot, $Workspace, $Tools, $ScriptsDir, $Logs, $TempDir)
        $Entries = $CurrentPath -split ";"
        $NewEntries = $Entries | Where-Object {
            $entry = $_.Trim()
            $shouldRemove = $false
            foreach ($ToRemove in $PathsToRemove) {
                if ($entry -eq $ToRemove) {
                    $shouldRemove = $true
                    break
                }
            }
            -not $shouldRemove
        }
        $CleanPath = ($NewEntries | Where-Object { $_ -and $_.Trim() -ne "" }) -join ";"
        [Environment]::SetEnvironmentVariable("Path", $CleanPath, "User")
        Write-OK "Entradas do PATH removidas."
        Log-Message "Entradas do PATH removidas."
    }
    catch {
        Write-Warn "Nao foi possivel limpar o PATH."
    }

    # Remover Launcher
    $LauncherDir = "$ScriptsDir\AdminLauncher"
    if (Test-Path $LauncherDir) {
        Remove-Item $LauncherDir -Recurse -Force
        Write-OK "Launcher removido."
        Log-Message "Launcher removido."
    }

    # Remover diretorios de desenvolvimento
    if (Test-Path $DevRoot) {
        Remove-Item $DevRoot -Recurse -Force
        Write-OK "Pastas de desenvolvimento removidas (C:\Dev)."
        Log-Message "Diretorio C:\Dev removido."
    }
    else {
        Write-Info "C:\Dev nao existe - nada para remover."
    }

    Write-Host ""
    Write-OK "Restauracao concluida."
    Write-Host ""
    Write-Warn "Reinicie o Windows para que todas as alteracoes de"
    Write-Warn "ambiente sejam completamente reconhecidas."

    Log-Message "=== DEV MODE - Restauracao concluida ==="
}

# =====================================================================
# MENU PRINCIPAL
# =====================================================================

$Running = $true

while ($Running) {

    Clear-Host

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "              ECO SYSTEM DEV MODE v2.0" -ForegroundColor Cyan
    Write-Host "                    WINDOWS 10" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "  [1]  Aplicar DEV MODE completo"
    Write-Host "  [2]  Criar estrutura de desenvolvimento"
    Write-Host "  [3]  Configurar PowerShell"
    Write-Host "  [4]  Configurar PATH"
    Write-Host "  [5]  Configurar permissoes do workspace"
    Write-Host "  [6]  Detectar ferramentas"
    Write-Host "  [7]  Inicializar logs"
    Write-Host "  [8]  Criar launcher administrativo"
    Write-Host "  [9]  Atualizar ambiente da sessao"
    Write-Host " [10]  Diagnostico completo"
    Write-Host " [11]  Verificar integridade"
    Write-Host " [12]  Restaurar configuracoes"
    Write-Host " [ 0]  Sair"
    Write-Host ""

    $Option = Read-Host "Escolha"

    switch ($Option) {

        "1"  { Apply-DevMode; Pause-DevMode }
        "2"  { Initialize-DevDirectories; Pause-DevMode }
        "3"  { Configure-PowerShell; Pause-DevMode }
        "4"  { Configure-Path; Pause-DevMode }
        "5"  { Set-DevPermissions; Pause-DevMode }
        "6"  { Detect-AllTools; Pause-DevMode }
        "7"  { Initialize-Logs; Pause-DevMode }
        "8"  { Create-ElevatedLauncher; Pause-DevMode }
        "9"  { Update-SessionEnvironment; Pause-DevMode }
        "10" { Run-Diagnostics; Pause-DevMode }
        "11" { Test-DevModeIntegrity; Pause-DevMode }
        "12" { Restore-DevMode; Pause-DevMode }

        "0" {
            Write-Host ""
            Write-Host "DEV MODE v2.0 encerrado." -ForegroundColor Cyan
            Log-Message "DEV MODE v2.0 encerrado pelo usuario"
            $Running = $false
            continue
        }

        default {
            Write-Host ""
            Write-Fail "Opcao invalida."
            Start-Sleep -Seconds 1
        }
    }
}