---
tipo: padrao
tags: [adb, android, debug, perito, skill, mcp, mobile, voxumgrau]
data: 2026-08-05
contexto: Jarvis solicitado a se tornar perito em ADB. Estudou help completo e sub-comandos.
decisao: Criar skill `mcp/android/habilidades/adb-perito/SKILL.md` consolidando todo conhecimento operacional de ADB.
impacto: Jarvis pode operar ADB com proficiencia de especialista — instalar apps, depurar, automatizar UI, capturar tela/video, inspecionar sistema, fazer backup, root, sideload. Acessivel via TTS/memory do ecossistema.
---

# ADB Perito — Skill Completo

## Motivo
Usuario pediu para Jarvis aprender tudo sobre ADB e se tornar eximio operador.

## O que foi feito
1. Capturado `adb help` completo (200+ linhas) — todas flags, sub-comandos, opcoes
2. Capturado `adb shell pm help` — gerenciador de pacotes (list, install, grant, revoke, clear, enable, disable, path, dump, list permissions/features/instrumentation/users)
3. Capturado `adb shell am help` — activity manager (start, broadcast, force-stop, start-service, instrument, compact, set-debug-app)
4. Capturado `adb shell input help` — tap, swipe, text, keyevent, keycombination, draganddrop, motionevent
5. Capturado `adb shell dumpsys -l` — lista 200+ servicos (activity, battery, clipboard, cpuinfo, gfxinfo, meminfo, notification, power, SurfaceFlinger, window, etc.)
6. Capturado `adb logcat --help` — options e filters (buffers, formatos, rotativ, file output, wrap)
7. Capturado `adb shell screencap --help` e `screenrecord --help` — captura PNG e gravacao MP4 (4M default bitrate, 180s max)
8. Capturado `adb shell wm help` — size, density, scaling, rotation, dismiss-keyguard
9. Capturado `adb shell svc help` — power, usb, nfc, system-server
10. Capturado `adb shell settings` — system/secure/global get/put/delete/reset/list
11. Capturado `adb shell content` — CRUD em ContentProviders (insert/update/delete/query/call/read)
12. Capturado `adb shell uiautomator help` — dump XML, runtest
13. Capturado `adb shell monkey` — stress test, intent seeds, scripts, port
14. Registrado tudo em `mcp/android/habilidades/adb-perito/SKILL.md` (500+ linhas)

## Outcome Operacional
Jarvis agora pode:
- Diagnosticar VoxUmGrau via `dumpsys meminfo` + `logcat -s VoxUmGrau:*`
- Instalar builds automaticamente (`adb install -r -g`)
- Controlar UI via `input tap`/`swipe`/`keyevent`
- Capturar evidencias com `screencap`/`screenrecord`
- Forcar permissões via `pm grant`
- Executar intents via `am start`
- Fazer debugging profundo com `logcat -v threadtime --pid=PID`
- Stress test com `monkey`
- Gerar bug reports com `adb bugreport`
- Diagnosticar rede, bateria, memoria, CPU, rendering (gfxinfo, graphicsstats)

## Acesso rapido
- Skill: `mcp/android/habilidades/adb-perito/SKILL.md`
- ADB instalado: `C:\Users\David Jr\AppData\Local\Android\platform-tools\platform-tools\adb.exe` (v1.0.41, 37.0.1-15733141)
- Dispositivo: Redmi Note 11 via Tailscale `100.64.71.9:5555`
- Display ID do dispositivo: 4630946773257169537

## Memoravel
"Enviar `adb help` para `Select-Object -First 200` captura tudo num comando so. Cada sub-comando (`pm`, `am`, `input`...) tem seu proprio help — chamados em paralelo pouparam saltos. Documentacao online `developer.android.com/tools/adb` esta fora do ar neste momento, mas o help offline e suficiente para pericia completa."
