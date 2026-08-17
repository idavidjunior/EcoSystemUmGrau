@echo off
REM ============================================================
REM  grafico_widget.bat - Widget do grafo do conhecimento (silencioso)
REM  Abre o widget SEM janela de terminal (usa pythonw).
REM  Tecle o widget para mover/redimensionar. Botao direito > controles.
REM  Encerre via Gerenciador de Tarefas ou 'feche o processo pythonw'.
REM ============================================================
setlocal
cd /d "%~dp0"
for /f "delims=" %%i in ('where pythonw 2^>nul') do (
    start "" "%%i" "%~dp0widget_grafo.py"
    goto :eof
)
start "" pythonw "%~dp0widget_grafo.py"
endlocal
