@echo off
rem Launcher do Guardiao do OpenCode Desktop
rem Monitora o desktop, previne fechamento por memoria e reinicia com flags de GPU se cair.
powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0opencode_desktop_guardian.ps1"
