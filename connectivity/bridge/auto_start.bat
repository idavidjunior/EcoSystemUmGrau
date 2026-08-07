@echo off
title EcoSystemUmGrau Bridge Resilience
:: Auto-start script for Windows startup folder
cd /d "C:\Users\David Jr\Documents\Default Project"

:: Verifica se já está rodando
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq Universal Bridge" | findstr python >nul 2>&1
if %errorlevel%==0 (
    echo Bridge daemon já em execução
    exit /b 0
)

:: Inicia o daemon oculto
start "Universal Bridge" /B /MIN python -c ^
    "import time; from EcoSystemUmGrau.connectivity.bridge.universal_bridge import UniversalBridge; b=UniversalBridge(); b.run_daemon(15)" 2>nul

echo Bridge daemon iniciado
