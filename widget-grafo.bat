@echo off
REM ============================================================
REM  widget-grafo.bat — abre o widget "Cerebro Vivo" sem janela
REM  de console. Usa pythonw.exe (modo janela) para suprimir o
REM  terminal do Python e deixar apenas a janela do grafo.
REM ============================================================
setlocal
set "ROOT=%~dp0"
where pythonw >nul 2>&1
if %errorlevel% equ 0 (
  start "" pythonw "%ROOT%scripts\widget_grafo.py"
) else (
  REM fallback: Python instalado via Microsoft Store (pythonw.exe)
  pythonw "%ROOT%scripts\widget_grafo.py"
)
endlocal
