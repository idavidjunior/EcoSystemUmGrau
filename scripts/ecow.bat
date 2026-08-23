@echo off
REM ============================================================
REM  ecow.bat - Abre o widget Cerebro Vivo (grafo 3D)
REM  Se ja estiver rodando, a nova instancia foca a janela
REM  existente e sai (comportamento dentro do widget_grafo.py)
REM ============================================================
setlocal
set "ROOT=%~dp0.."
where pythonw >nul 2>&1
if %errorlevel% equ 0 (
  start "" pythonw "%ROOT%\scripts\widget_grafo.py"
) else (
  where python >nul 2>&1
  if %errorlevel% equ 0 (
    start "" python "%ROOT%\scripts\widget_grafo.py"
  ) else (
    echo Python nao encontrado no PATH.
  )
)
endlocal
