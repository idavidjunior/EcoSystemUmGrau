@echo off
REM ============================================================
REM  reiniciarjarvis.bat - Reinicia narrador, widget e bridge
REM  Uso: reiniciarjarvis
REM ============================================================
setlocal
set "ROOT=%~dp0.."

echo [reiniciarjarvis] Parando narrador...
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq narrador*" 2>nul
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq widget*" 2>nul

REM Para bridge TTS ativa (flag + jarvis_audio stop)
if exist "%ROOT%\runtime\parar_fala.flag" (
    echo [reiniciarjarvis] Sinalizando parada de fala...
    echo %DATE% %TIME% > "%ROOT%\runtime\parar_fala.flag"
)
python "%ROOT%\scripts\jarvis_audio.py" stop 2>nul

echo [reiniciarjarvis] Aguardando processos finalizarem...
timeout /t 2 /nobreak >nul

echo [reiniciarjarvis] Iniciando Widget Edge (Narrador integrado)...
start "WidgetEdge" /B pythonw "%~dp0widget_edge.py"

echo [reiniciarjarvis] Iniciando Cerebro Vivo...
start "CerebroVivo" /B pythonw "%~dp0widget_grafo.py"

echo [reiniciarjarvis] Pronto.
endlocal