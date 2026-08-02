@echo off
title EcoSystemUmGrau - Setup Plug & Play
chcp 65001 >nul

echo ====================================================
echo   EcoSystemUmGrau - Setup Automatico
echo   Plug ^& Play: instala tudo em qualquer PC novo
echo   Fonte unica: github.com/idavidjunior/EcoSystemUmGrau
echo ====================================================
echo.

:: ─── Verificar requisitos ──────────────────────────────
where /q git || (
    echo [ERRO] Git nao encontrado. Instale https://git-scm.com/
    pause & exit /b 1
)
where /q node || (
    echo [ERRO] Node.js nao encontrado. Instale https://nodejs.org/
    pause & exit /b 1
)
where /q python || (
    echo [ERRO] Python nao encontrado. Instale https://python.org/
    pause & exit /b 1
)
echo [OK] Git, Node.js, Python detectados
echo.

:: ─── Diretorios ─────────────────────────────────────────
set ECO_DIR=%USERPROFILE%\Documents\Default Project\EcoSystemUmGrau
set LER_DIR=%ECO_DIR%\ler-runtime
set OCODE_DIR=%USERPROFILE%\.config\opencode
set AGENTS_SRC=%ECO_DIR%\config\agents
set PROFILE_DIR=%USERPROFILE%\Documents\WindowsPowerShell
set PROFILE_PS1=%PROFILE_DIR%\profile.ps1

:: ─── 1. Clonar Ecosistema ───────────────────────────────
if exist "%ECO_DIR%\.git" (
    echo [1/7] EcoSystemUmGrau ja clonado, atualizando...
    git -C "%ECO_DIR%" pull --ff-only
) else (
    echo [1/7] Clonando EcoSystemUmGrau...
    if not exist "%ECO_DIR%" mkdir "%ECO_DIR%"
    git clone https://github.com/idavidjunior/EcoSystemUmGrau.git "%ECO_DIR%"
)
echo.

:: ─── 2. Instalar OpenCode ──────────────────────────────
echo [2/7] Verificando OpenCode...
npm list -g opencode-ai >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando OpenCode (npm i -g opencode-ai)...
    call npm i -g opencode-ai
) else ( echo [OK] OpenCode ja instalado )
echo.

:: ─── 3. Gerar config OpenCode a partir do template ─────
echo [3/7] Gerando configuracao do OpenCode...
if not exist "%OCODE_DIR%" mkdir "%OCODE_DIR%"
if not exist "%OCODE_DIR%\agents" mkdir "%OCODE_DIR%\agents"

:: Converter USERPROFILE para forward slashes (C:\Users\X -> C:/Users/X)
for /f "delims=" %%i in ("%USERPROFILE%") do set UP=%%i
set UP_FS=%UP:\=/%

:: Gerar opencode.jsonc do template
powershell -Command ^
    "$t = Get-Content '%ECO_DIR%\config\opencode.jsonc' -Raw; " ^
    "$t = $t.Replace('{{USERPROFILE}}', '%UP_FS%'); " ^
    "Set-Content '%OCODE_DIR%\opencode.jsonc' -Value $t -Encoding UTF8 -Force"
if %errorlevel% equ 0 ( echo [OK] opencode.jsonc gerado ) else ( echo [ERRO] ao gerar config & pause & exit /b 1 )

:: Copiar fallback config
copy /Y "%ECO_DIR%\config\opencode-model-fallback.jsonc" "%OCODE_DIR%\" >nul
echo [OK] opencode-model-fallback.jsonc copiado

:: Copiar agents (fonte unica: repo)
xcopy /E /Y "%AGENTS_SRC%\*" "%OCODE_DIR%\agents\" >nul
echo [OK] Agents copiados (fonte: repo/config/agents/)
echo.

:: ─── 4. LER Runtime (vem dentro do repo) ────────────────
echo [4/7] Verificando LER runtime em %LER_DIR%...
if exist "%LER_DIR%\run.py" (
    echo [OK] LER runtime: %LER_DIR%
) else ( echo [AVISO] LER runtime nao encontrado em %LER_DIR%. Ja deve vir clonado. )
echo.

:: ─── 5. Instalar Plugin Fallback ───────────────────────
echo [5/7] Instalando plugin fallback...
set FALLBACK_DIR=%OCODE_DIR%\node_modules
if not exist "%FALLBACK_DIR%\@razroo\opencode-model-fallback" (
    if not exist "%FALLBACK_DIR%" mkdir "%FALLBACK_DIR%"
    pushd "%FALLBACK_DIR%"
    call npm init -y >nul 2>&1
    call npm install @razroo/opencode-model-fallback
    popd
    echo [OK] Plugin fallback instalado
) else ( echo [OK] Plugin fallback ja existe )
echo.

:: ─── 6. Profile PowerShell ─────────────────────────────
echo [6/7] Configurando profile PowerShell...
if not exist "%PROFILE_DIR%" mkdir "%PROFILE_DIR%"

findstr "start-vigilante" "%PROFILE_PS1%" >nul 2>&1
if %errorlevel% neq 0 (
    (
        echo.
        echo # ============================================================
        echo # EcoSystemUmGrau - Gerado por setup.bat
        echo # ============================================================
        echo $env:Path = "C:\Program Files\GitHub CLI;$env:Path"
        echo.
        echo function start-vigilante {
        echo     $script = "%ECO_DIR%\scripts\vigilante.ps1"
        echo     if ^(Test-Path $script^) { Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$script`"" -WindowStyle Hidden }
        echo     else { Write-Host "[ERRO] vigilante.ps1 nao encontrado" -ForegroundColor Red }
        echo }
        echo function stop-vigilante  { powershell -NoProfile -ExecutionPolicy Bypass -File "%ECO_DIR%\scripts\vigilante.ps1" -Stop }
        echo function status-vigilante { powershell -NoProfile -ExecutionPolicy Bypass -File "%ECO_DIR%\scripts\vigilante.ps1" -Status }
        echo function ecosystem {
        echo     $script = "%ECO_DIR%\scripts\ecosystem.ps1"
        echo     if ^(Test-Path $script^) { ^& $script @args }
        echo     else { Write-Host "[ERRO] ecosystem.ps1 nao encontrado" -ForegroundColor Red }
        echo }
        echo.
        echo start-vigilante
    ) >> "%PROFILE_PS1%"
    echo [OK] Funcoes adicionadas
) else ( echo [OK] Profile ja configurado )
echo.

:: ─── 7. API Keys ───────────────────────────────────────
echo [7/7] Configurar chaves de API (ENTER para pular)
echo.

set /p NVIDIA_KEY="  NVIDIA API Key: "
if not "%NVIDIA_KEY%"=="" (
    powershell -Command "[Environment]::SetEnvironmentVariable('NVIDIA_API_KEY', '%NVIDIA_KEY%', 'User')"
    echo $env:NVIDIA_API_KEY = '%NVIDIA_KEY%' >> "%PROFILE_PS1%"
    echo [OK] NVIDIA_API_KEY salva
)

set /p OPENAI_KEY="  OpenAI API Key: "
if not "%OPENAI_KEY%"=="" (
    powershell -Command "[Environment]::SetEnvironmentVariable('OPENAI_API_KEY', '%OPENAI_KEY%', 'User')"
    echo $env:OPENAI_API_KEY = '%OPENAI_KEY%' >> "%PROFILE_PS1%"
    echo [OK] OPENAI_API_KEY salva
)

set /p GITHUB_TOKEN="  GitHub Token: "
if not "%GITHUB_TOKEN%"=="" (
    powershell -Command "[Environment]::SetEnvironmentVariable('GH_TOKEN', '%GITHUB_TOKEN%', 'User')"
    echo $env:GH_TOKEN = '%GITHUB_TOKEN%' >> "%PROFILE_PS1%"
    echo [OK] GH_TOKEN salva
)

:: ─── 8. Validar config ─────────────────────────────────
echo [8/8] Validando config OpenCode...
call opencode debug config >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Config OpenCode valida
) else (
    echo [AVISO] opencode debug config reportou erro. Verifique manualmente.
)

echo.
echo ====================================================
echo   Setup concluido!
echo.
echo   Proximos passos:
echo     1. Feche e reabra o PowerShell
echo     2. Teste: opencode --version
echo     3. Status: ecosystem status
echo     4. Sync:  ecosystem sync
echo     5. Scan:  ecosystem scan
echo     6. Use:   opencode
echo.
echo   Repositorio: https://github.com/idavidjunior/EcoSystemUmGrau
echo ====================================================
pause
