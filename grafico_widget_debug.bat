@echo off
REM ============================================================
REM  grafico_widget_debug.bat - Widget do grafo (MODO DEBUG)
REM  Abre o widget COM janela de terminal (python.exe) para ver logs.
REM  Feche fechando a janela de terminal (ou Ctrl+C).
REM ============================================================
setlocal
cd /d "%~dp0"
python "%~dp0scripts\widget_grafo.py"
endlocal