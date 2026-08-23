@echo off
REM ============================================================
REM  ecow.bat - Abre o widget Cerebro Vivo (grafo 3D)
REM  Se ja estiver rodando, a nova instancia foca a janela
REM  existente e sai (comportamento dentro do widget_grafo.py)
REM ============================================================
setlocal
set "ROOT=%~dp0.."
REM Somente pythonw: nunca abre console de terminal.
where pythonw >nul 2>&1
if %errorlevel% equ 0 (
  start "" pythonw "%ROOT%\scripts\widget_grafo.py"
) else (
  echo Pythonw nao encontrado no PATH. Widget nao iniciado.
  exit /b 1
)
endlocal
