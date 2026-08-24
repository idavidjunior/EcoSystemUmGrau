<# 
.SYNOPSIS
    Cria atalho "Cerebro Vivo" na Area de Trabalho e/ou Menu Iniciar
    com icone personalizado para o widget do grafo 3D.
#>

param(
    [switch]$Desktop,
    [switch]$StartMenu,
    [switch]$Taskbar
)

$ROOT = "$PSScriptRoot\.."
$SCRIPT = "$ROOT\scripts\widget_grafo.py"
$ICON_SRC = "$ROOT\assets\jarvis.ico"

# Se nao existe icone, criar um simples ou usar o padrao do Python
if (-not (Test-Path $ICON_SRC)) {
    Write-Host "Icone nao encontrado em $ICON_SRC, usando padrao..." -ForegroundColor Yellow
    $ICON_SRC = "$env:SystemRoot\System32\shell32.dll,13"  # icone generico
}

$WSH = New-Object -ComObject WScript.Shell

# Area de Trabalho
if ($Desktop -or (-not $StartMenu -and -not $Taskbar)) {
    $DESKTOP_DIR = [Environment]::GetFolderPath('Desktop')
    $LNK_DESKTOP = Join-Path $DESKTOP_DIR "Cerebro Vivo.lnk"
    $shortcut = $WSH.CreateShortcut($LNK_DESKTOP)
    $shortcut.TargetPath = "pythonw.exe"
    $shortcut.Arguments = "`"$SCRIPT`""
    $shortcut.WorkingDirectory = $ROOT
    $shortcut.IconLocation = $ICON_SRC
    $shortcut.Description = "Widget Cerebro Vivo - Grafo 3D do conhecimento"
    $shortcut.Save()
    Write-Host "[OK] Atalho criado na Area de Trabalho: $LNK_DESKTOP" -ForegroundColor Green
}

# Menu Iniciar
if ($StartMenu) {
    $START_DIR = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
    $LNK_START = Join-Path $START_DIR "Cerebro Vivo.lnk"
    $shortcut = $WSH.CreateShortcut($LNK_START)
    $shortcut.TargetPath = "pythonw.exe"
    $shortcut.Arguments = "`"$SCRIPT`""
    $shortcut.WorkingDirectory = $ROOT
    $shortcut.IconLocation = $ICON_SRC
    $shortcut.Description = "Widget Cerebro Vivo - Grafo 3D do conhecimento"
    $shortcut.Save()
    Write-Host "[OK] Atalho criado no Menu Iniciar: $LNK_START" -ForegroundColor Green
}

# Fixar na Taskbar (requer Windows 10/11 + direitos)
if ($Taskbar) {
    Write-Host "Para fixar na Taskbar: clique com botao direito no atalho da Area de Trabalho > 'Fixar na barra de tarefas'" -ForegroundColor Cyan
    Write-Host "Ou arraste o atalho do Menu Iniciar para a Taskbar." -ForegroundColor Cyan
}

Write-Host "`nUse: .\criar_atalho_cerebro.ps1 -Desktop -StartMenu" -ForegroundColor Gray