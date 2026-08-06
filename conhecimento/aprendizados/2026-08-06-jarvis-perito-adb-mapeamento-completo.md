---
tipo: padrao
tags: [adb, android, xiaomi, redmi-note-11, automacao, ui, perito]
data: 2026-08-06
contexto: O usuario pediu para o Jarvis se tornar um perito em ADB — estudar tudo, catalogar capacidade e se tornar eximio operador. Mapeamento feito rodando comandos reais no Redmi Note 11 do usuario.
decisao: Jarvis agora e operador ADB nivel perito. Conhecimento consolidado neste arquivo serve de referencia rapida para qualquer tarefa futura envolvendo ADB no ecossistema.
impacto: Qualquer automacao Android (build, install, UI tap, screenshot, statusbar, app launch, file pull/push, bateria, props, logcat) pode ser executada diretamente pelo Jarvis sem pesquisa adicional. Script adb-redmi.ps1 ja garante conexao Tailscale automatica.
---

# Jarvis — Perito ADB

## Ambiente mapeado (06/08/2026)

- **Host**: Windows 10.0.19045, ADB 1.0.41 (37.0.1-15733141) em `%LOCALAPPDATA%\Android\platform-tools\platform-tools\adb.exe`
- **Device**: Xiaomi Redmi Note 11 (`2201117TI`, codinome `spes`), Android 13, SDK 33, ABI arm64-v8a, heap 256m
- **Conexao**: Tailscale `100.64.71.9:5555` (transport_id:5) — `scripts/adb-redmi.ps1` descobre rota automaticamente
- **Tela**: 1080x2400, densidade 440 (override 461)

## Capacidades ADB confirmadas em campo

### Dispositivo e sistema
- `adb devices -l` — lista com produto, modelo, dispositivo, transport_id
- `adb shell getprop <chave>` — qualquer propriedade (ro.product.*, ro.build.*, dalvik.vm.*, etc.)
- `adb shell dumpsys battery` — status, saude, nivel, temperatura, corrente
- `adb shell dumpsys <servico>` — bateria, activity, window, package, power, notification, input...
- `adb shell wm size` / `wm density` — resolucao e densidade
- `adb shell getprop` (sem arg) — todas as propriedades de uma vez

### Gerenciamento de pacotes (pm)
- `adb shell pm list packages` — todos (342 no Redmi)
- `adb shell pm list packages -3` — terceiros (78 no Redmi, incluindo com.voxumgrau.app, com.supermarket.calculator, com.biblia.estudo, com.mp3player.debug)
- `adb shell pm list packages -s` — system apps
- `adb shell pm path <package>` — caminho do APK instalado (ex: `/system_ext/priv-app/Settings/Settings.apk`)
- `adb shell pm install [-r] [-d] [-t] <apk>` — instalar; `-r` reinstala mantendo dados, `-d` permite downgrade, `-t` test
- `adb install [-r] [-d] [-t] <apk_local>` — instalar APK do PC no celular
- `adb install -g <apk>` — concede todas as permissoes do manifest apos instalar
- `adb install --instant <apk>` — instala como app efemero (instant app)
- `adb install --fastdeploy <apk>` — deploy rapido (so patch, deltas)
- `adb install --no-streaming <apk>` — push APK separado do invoke PM (mais lento, mais compativel)
- `adb install-multiple a.apk b.apk` — varios APKs de um unico pacote (split APKs)
- `adb install-multi-package a.apk b.apk` — varios pacotes atomicos (transacao all-or-nothing)
- `adb uninstall <package>` — desinstalar
- `adb shell cmd package list packages -3` — alternativa ao pm

### Port forwarding (redirecionamento de portas)
- `adb forward tcp:6123 tcp:7123` — PC:6123 → celular:7123 (TCP)
- `adb forward --list` — lista todos os forwards ativos
- `adb forward --remove tcp:6123` — remove forward especifico
- `adb forward --remove-all` — remove todos
- `adb forward tcp:LOCAL abstract-local:REMOTE` — socket Unix abstrato
- Usado pra debug de apps que rodam servidor no celular (gdbserver, servidores custom)

### Automacao de UI (input / uiautomator) — capacidade-chave de perito
- `adb shell input tap <x> <y>` — toque na coordenada (resolucao 1080x2400)
- `adb shell input swipe <x1> <y1> <x2> <y2> <ms>` — deslize com duracao
- `adb shell input text "<string>"` — digitar texto em campo focado
- `adb shell input keyevent <CODE>` — emular tecla (KEYCODE_HOME, KEYCODE_BACK, KEYCODE_POWER, KEYCODE_VOLUME_UP, KEYCODE_MENU, KEYCODE_ENTER...)
- `adb shell uiautomator dump /sdcard/ui.xml` — dump da hierarquia XML da tela atual (12-84 KB tipico). No MIUI gera aviso de ThemeCompatibility mas o dump funciona
- Fluxo completo de automacao: `uiautomator dump` → `adb pull` → parsear XML → `input tap/swipe` no elemento

### Captura de tela e gravacao
- `adb shell screencap -p /sdcard/file.png` — screenshot PNG
- `adb shell screenrecord [--time-limit N] /sdcard/file.mp4` — gravar tela (max 180s default)
- `adb pull /sdcard/file.png .` — transferir para o PC
- `adb shell ls -la /sdcard/file.png` — verificar existencia e tamanho

### Transferencia de arquivos
- `adb push <local> /sdcard/` — PC → celular
- `adb pull /sdcard/<arquivo> <local>` — celular → PC (rapido, ~0.4 MB/s ja medido)
- `adb shell ls -la /sdcard/` — navegar filesystem do celular

### Logcat e debug
- `adb logcat` — log em tempo real (Ctrl+C para)
- `adb logcat -d` — dump e sai (nao fica preso)
- `adb logcat -d *:E` — so erros
- `adb logcat -d | Select-String "<tag>"` — filtrar tag
- `adb logcat -c` — limpar buffer
- `adb bugreport bugreport.zip` — relatorio completo de diagnostico (lento, varios MB)

### Status bar e system UI
- `adb shell cmd statusbar expand-notifications` — abrir painel de notificacoes
- `adb shell cmd statusbar expand-settings` — abrir painel de config rapida
- `adb shell cmd statusbar collapse` — fechar painel
- `adb shell am start -n <pkg>/<activity>` — abrir activity diretamente
- `adb shell am start -a android.intent.action.VIEW -d <url>` — abrir URL
- `adb shell am force-stop <pkg>` — matar app
- `adb shell am kill <pkg>` — matar processo (mais suave)

### Conexao e wireless debugging (ja documentado em aprendizado anterior)
- `adb tcpip 5555` — modo TCP (nao persiste apos reboot — precisa USB de novo ou Wireless Debugging)
- `adb pair <ip>:<porta_pareamento> <codigo>` — pareamento Android 11+
- `adb connect <ip>:<porta_conexao>` — conectar apos pareamento
- `adb mdns services` — descobrir portas `_adb-tls-pairing._tcp` e `_adb-tls-connect._tcp`
- `adb disconnect` — desconectar
- `adb kill-server` — reinicia servidor ADB (cuidado: pode derrubar o shell atual)
- `adb start-server` — inicia servidor

### Build e deploy (usado pelo VoxUmGrau e apps irmaos)
- `adb install -r -d <apk>` — reinstalar mantendo dados, permite downgrade
- Para assinatura diferente: desinstalar primeiro (`adb uninstall`) e instalar limpo
- `.\build.ps1 -Install` no Android/VoxUmGrau chama adb install automaticamente
- MIUI: apos `adb install`, aguardar 3s e aceitar dialog "Permitir" com `adb shell input tap <x> <y>` (ver aprendizado bugs/permission-dialogs-do-miui)

### Backup e dados
- `adb shell run-as <pkg>` — acessar dados de app debuggueable
- `adb backup -f <file.ab> <pkg>` — backup de app (requer confirmacao na tela)
- `adb shell settings get <namespace>/<key>` — ler settings (system, secure, global)
- `adb shell settings put <namespace>/<key> <value>` — alterar setting

## Padroes de operacao para o Jarvis

1. **Sempre verificar conexao primeiro**: `adb devices -l` antes de qualquer acao
2. **Caminho do adb**: `%LOCALAPPDATA%\Android\platform-tools\platform-tools\adb.exe` — usar `scripts/adb-redmi.ps1` para descobrir rota Tailscale automaticamente
3. **UI automacao**: uiautomator dump → pull → parsear com parser XML → input tap — eh o caminho mais rapido (sem Appium)
4. **PowerShell noWindows**: `&` para background NAO funciona — usar `Start-Job` ou rodar em processo separado. Sempre terminar comando sem `&`
5. **Cuidado com kill-server**: pode derrubar o shell que o executa — rodar em processo separado
6. **MIUI dialogs**: apos install, aguardar 3s e aceitar dialog "Permitir" com input tap coordenado (botao "Permitir" tipicamente em ~800x1500)
7. **Reconectar apos reboot do celular**: `adb tcpip 5555` nao persiste — precisa USB ou Wireless Debugging (`adb pair`)
