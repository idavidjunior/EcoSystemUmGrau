@echo off
REM ============================================================
REM  controle.bat - Janela flutuante de controle da voz Jarvis
REM  Abre COM janela de console (usa python.exe, modo console).
REM  Materializa a voz do opencode-desktop: controla a narracao
REM  (voz ON/OFF), interrompe a fala (STOP) e liga/desliga o
REM  microfone (dialogo.py --modo vad).
REM  Tecle o widget para mover/redimensionar.
REM ============================================================
setlocal
set "ROOT=%~dp0.."
where python >nul 2>&1
if %errorlevel% equ 0 (
  start "" python "%ROOT%\scripts\widget_controle_jarvis.py"
) else (
  REM fallback: Python via Microsoft Store
  python "%ROOT%\scripts\widget_controle_jarvis.py"
)
endlocal
