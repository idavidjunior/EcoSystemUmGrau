@echo off
rem Launcher do Watchdog do EcoSystemUmGrau
rem Usado pelo atalho de Startup e por tarefa agendada (opcional).
powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0watchdog.ps1"
