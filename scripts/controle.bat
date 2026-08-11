@echo off
REM ============================================================
REM  controle.bat - Janela flutuante de controle da voz Jarvis
REM  Abre SEM janela de console (usa pythonw.exe, modo janela).
REM  Materializa a voz do opencode-desktop: controla a narracao
REM  (voz ON/OFF), interrompe a fala (STOP) e liga/desliga o
REM  microfone (dialogo.py --modo vad).
REM  Tecle o widget para mover/redimensionar.
REM ============================================================
setlocal
set "ROOT=%~dp0.."
where pythonw >nul 2>&1
if %errorlevel% equ 0 (
  start "" pythonw "%ROOT%\scripts\widget_controle_jarvis.py"
) else (
  REM fallback: Python via Microsoft Store
  pythonw "%ROOT%\scripts\widget_controle_jarvis.py"
)
endlocal
