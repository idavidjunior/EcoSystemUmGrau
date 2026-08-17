@echo off
REM ============================================================
REM  opencode-wrapper.bat — roda opencode com narração em áudio
REM  obrigatória (edge-tts + MCI). Toda resposta do agente é
REM  narrada em voz (pt-BR-AntonioNeural).
REM ============================================================
setlocal
set "ROOT=%~dp0"
set "PY=%ROOT%..\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%ROOT%scripts\opencode_wrapper.py" %*
endlocal
