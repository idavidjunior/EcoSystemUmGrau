@echo off
REM ============================================================
REM  controle.bat - Abre o widget oficial Edge
REM  Unico widget do ecossistema: scripts/widget_edge.py
REM ============================================================
setlocal
set "ROOT=%~dp0.."
where pythonw >nul 2>&1
if %errorlevel% equ 0 (
  start "" pythonw "%ROOT%\scripts\widget_edge.py"
) else (
  where python >nul 2>&1
  if %errorlevel% equ 0 (
    start "" python "%ROOT%\scripts\widget_edge.py"
  ) else (
    echo Python nao encontrado no PATH.
  )
)
endlocal
