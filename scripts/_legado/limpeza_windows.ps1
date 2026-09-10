<#
.SYNOPSIS
    Limpeza profunda do Windows: Update cache, temp, logs, lixo do sistema.
.DESCRIPTION
    Remove tudo que é seguro apagar: Windows Update cache, Delivery Optimization,
    temp folders, prefetch, logs antigos, thumbnails, error reports, etc.
.NOTES
    Requer PowerShell como Administrador para limpar pastas do sistema.
    Rode com: powershell -ExecutionPolicy Bypass -File limpeza_windows.ps1
#>

param(
    [switch]$DryRun,
    [switch]$Verbose,
    [int]$LogMaxAgeDays = 30,
    [int]$TempMaxAgeDays = 7
)

$ErrorActionPreference = "Continue"

function Write-Log {
    param($Msg, $Level = "INFO")
    $line = "[$(Get-Date -Format 'HH:mm:ss')] [$Level] $Msg"
    $logFile = "$env:USERPROFILE\.limpeza_windows.log"
    Add-Content -Path $logFile -Value $line -Encoding UTF8
    Write-Host $line
}

function Get-FolderSize {
    param($Path)
    if (-not (Test-Path $Path)) { return 0 }
    try {
        $size = (Get-ChildItem $Path -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        return $size
    } catch { return 0 }
}

function Format-Bytes {
    param([long]$Bytes)
    if ($Bytes -ge 1GB) { return "{0:N2} GB" -f ($Bytes/1GB) }
    if ($Bytes -ge 1MB) { return "{0:N2} MB" -f ($Bytes/1MB) }
    if ($Bytes -ge 1KB) { return "{0:N2} KB" -f ($Bytes/1KB) }
    return "$Bytes B"
}

function Clean-Path {
    param($Path, $Description, $MaxAgeDays = 0, $Recurse = $true)
    if (-not (Test-Path $Path)) {
        Write-Log "[$Description] Não existe: $Path" "WARN"
        return 0
    }
    $before = Get-FolderSize $Path
    if ($before -eq 0) {
        Write-Log "[$Description] Já vazio: $Path"
        return 0
    }
    Write-Log "[$Description] Limpando: $Path (tamanho: $(Format-Bytes $before))"
    if ($DryRun) {
        Write-Log "  [DRY-RUN] Removeria: $Path"
        return $before
    }
    try {
        $items = Get-ChildItem $Path -Recurse:$Recurse -Force -ErrorAction SilentlyContinue
        if ($MaxAgeDays -gt 0) {
            $cutoff = (Get-Date).AddDays(-$MaxAgeDays)
            $items = $items | Where-Object { $_.LastWriteTime -lt $cutoff }
        }
        $count = 0
        $items | ForEach-Object {
            try {
                Remove-Item $_.FullName -Force -Recurse -ErrorAction SilentlyContinue
                $count++
            } catch {}
        }
        $after = Get-FolderSize $Path
        $freed = $before - $after
        Write-Log "  OK: $count itens removidos, liberado $(Format-Bytes $freed) (restante: $(Format-Bytes $after))"
        return $freed
    } catch {
        Write-Log "  ERRO: $_" "ERROR"
        return 0
    }
}

# Precisa de Admin para pastas do sistema
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Log "AVISO: Script não roda como Administrador. Pastas do sistema (C:\Windows\*) não serão limpas." "WARN"
    Write-Log "Execute: powershell -ExecutionPolicy Bypass -File limpeza_windows.ps1 (como Admin)" "WARN"
}

Write-Log "=== LIMPEZA WINDOWS INICIADA ==="
if ($DryRun) { Write-Log "MODO DRY-RUN (apenas simula)" }

$totalFreed = 0

# 1. Windows Update Cache
Write-Log "--- Windows Update ---"
$totalFreed += Clean-Path "C:\Windows\SoftwareDistribution\Download" "Windows Update Download" 0
$totalFreed += Clean-Path "C:\Windows\SoftwareDistribution\DataStore\Logs" "Windows Update Logs" $LogMaxAgeDays

# 2. Delivery Optimization (peer-to-peer updates)
$totalFreed += Clean-Path "C:\Windows\ServiceProfiles\NetworkService\AppData\Local\DeliveryOptimization\Cache" "Delivery Optimization Cache" 0

# 3. Windows Temp
$totalFreed += Clean-Path "C:\Windows\Temp" "Windows Temp" $TempMaxAgeDays
$totalFreed += Clean-Path "C:\Temp" "C:\Temp" $TempMaxAgeDays

# 4. User Temp
$totalFreed += Clean-Path "$env:TEMP" "User Temp" $TempMaxAgeDays
$totalFreed += Clean-Path "$env:TMP" "User TMP" $TempMaxAgeDays

# 5. Prefetch (otimização de boot, seguro limpar)
$totalFreed += Clean-Path "C:\Windows\Prefetch" "Prefetch" $LogMaxAgeDays

# 6. Logs do sistema antigos
$totalFreed += Clean-Path "C:\Windows\Logs" "Windows Logs" $LogMaxAgeDays
$totalFreed += Clean-Path "C:\Windows\Panther" "Panther (setup logs)" $LogMaxAgeDays
$totalFreed += Clean-Path "C:\Windows\Memory.dmp" "Memory Dump" 0 $false
$totalFreed += Clean-Path "C:\Windows\Minidump" "Minidumps" $LogMaxAgeDays

# 7. Error Reporting
$totalFreed += Clean-Path "C:\ProgramData\Microsoft\Windows\WER\ReportArchive" "Error Reports Archive" $LogMaxAgeDays
$totalFreed += Clean-Path "C:\ProgramData\Microsoft\Windows\WER\ReportQueue" "Error Reports Queue" $LogMaxAgeDays
$totalFreed += Clean-Path "C:\Users\*\AppData\Local\Microsoft\Windows\WER" "User Error Reports" $LogMaxAgeDays

# 8. Thumbnails cache
$totalFreed += Clean-Path "C:\Users\*\AppData\Local\Microsoft\Windows\Explorer" "Thumbnails Cache" $LogMaxAgeDays $false

# 9. Windows Defender cache
$totalFreed += Clean-Path "C:\ProgramData\Microsoft\Windows Defender\Scans\History\Store" "Defender Scan History" $LogMaxAgeDays
$totalFreed += Clean-Path "C:\ProgramData\Microsoft\Windows Defender\Definition Updates\Backup" "Defender Definitions Backup" 0

# 10. Browser caches (Edge/Chrome/Firefox se existirem)
$browserCaches = @(
    "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache",
    "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache",
    "$env:APPDATA\Mozilla\Firefox\Profiles\*\cache2"
)
foreach ($cache in $browserCaches) {
    $totalFreed += Clean-Path $cache "Browser Cache" $TempMaxAgeDays
}

# 11. Windows Store cache
$totalFreed += Clean-Path "$env:LOCALAPPDATA\Packages\Microsoft.WindowsStore_*\LocalCache" "Windows Store Cache" $TempMaxAgeDays

# 12. OneDrive cache
$totalFreed += Clean-Path "$env:LOCALAPPDATA\Microsoft\OneDrive\logs" "OneDrive Logs" $LogMaxAgeDays
$totalFreed += Clean-Path "$env:LOCALAPPDATA\Microsoft\OneDrive\setup\logs" "OneDrive Setup Logs" $LogMaxAgeDays

# 13. Windows.old (se houver upgrade recente)
if (Test-Path "C:\Windows.old") {
    $size = Get-FolderSize "C:\Windows.old"
    if ($size -gt 0) {
        Write-Log "[Windows.old] Encontrado: $(Format-Bytes $size) - REMOVER MANUALMENTE se não precisar voltar versão anterior" "WARN"
    }
}

# 14. Recycle Bin
if (-not $DryRun) {
    try {
        $shell = New-Object -ComObject Shell.Application
        $recycle = $shell.Namespace(0xA)
        $recycle.Items() | ForEach-Object { $_.InvokeVerb("Delete") }
        Write-Log "[Lixeira] Esvaziada"
    } catch {}
}

# 15. Component Store (WinSxS) - apenas análise, não apagar
if ($isAdmin) {
    Write-Log "[WinSxS] Analisando component store..." "INFO"
    try {
        $dism = & dism /Online /Cleanup-Image /AnalyzeComponentStore 2>&1
        Write-Log "[WinSxS] $dism"
    } catch {}
}

Write-Log "=== LIMPEZA CONCLUÍDA ==="
Write-Log "Total liberado: $(Format-Bytes $totalFreed)"

if ($DryRun) {
    Write-Log "DRY-RUN: Nada foi realmente apagado. Rode sem -DryRun para executar." "WARN"
}