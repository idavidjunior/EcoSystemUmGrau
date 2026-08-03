@echo off
REM ============================================================
REM  grafico_widget.bat - Widget do grafo do conhecimento (silencioso)
REM  Abre o widget SEM janela de terminal (usa pythonw).
REM  Tecle o widget para mover/redimensionar. Botao direito > controles.
REM  Encerre via Gerenciador de Tarefas ou 'feche o processo pythonw'.
REM ============================================================
setlocal
cd /d "%~dp0"
start "" "C:\Users\David Jr\AppData\Local\Programs\Python\Python312\pythonw.exe" "%~dp0scripts\widget_grafo.py"
endlocal