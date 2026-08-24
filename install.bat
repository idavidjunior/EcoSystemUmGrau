@echo off
REM EcoSystemUmGrau — Instalador universal (Windows batch wrapper)
REM Uso: install.bat [--no-venv] [--check] [--sync]

set ECO_DIR=%USERPROFILE%\Documents\Default Project\EcoSystemUmGrau
cd /d "%ECO_DIR%"

python scripts\install.py %*
if errorlevel 1 (
    echo.
    echo [ERRO] Instalacao falhou. Verifique as mensagens acima.
    pause
    exit /b 1
)

echo.
echo [OK] Instalacao concluida com sucesso.
echo.
echo Para usar o ecossistema:
echo   python scripts\runtime_boot.py
echo.
pause