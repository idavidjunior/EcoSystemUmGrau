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

## Extensao perito (06/08/2026, sessao 2 — validacao completa)

### Activity Manager (am) — controle total de atividades
- `adb shell am start -n <pkg>/<activity>` — abrir activity explicita
- `adb shell am start -a android.intent.action.VIEW -d <url>` — intent VIEW com dado
- `adb shell am start -a android.intent.action.VIEW -d "geo:-23.5,-46.6" com.google.android.apps.maps` — intent especifica
- `adb shell am start -t <mimeType> -d <uri>` — intent com tipo MIME
- `adb shell am start --USER <user_id>` — abrir em perfil de trabalho (work profile)
- `adb shell am force-stop <pkg>` — forcar parada
- `adb shell am kill <pkg>` — matar processo suave
- `adb shell am kill-all` — matar todos processos background
- `adb shell am instrument -w <pkg.test>/<runner>` — rodar testes instrumentados (UI Automator, Espresso)
- `adb shell am broadcast -a android.intent.action.BOOT_COMPLETED` — simular broadcast
- `adb shell am startservice -n <pkg>/<service>` — iniciar servico
- `adb shell am stopservice -n <pkg>/<service>` — parar servico
- `adb shell am set-debug-app [-w] [--persistent] <pkg>` — marcar app pra debug (espera debugger com -w)

### Package Manager (pm) — Gestao avancada
- `adb shell pm list packages [-3|-s|-u|-d]` — filtros: terceiros/sistema/uninstalled/disabled
- `adb shell pm list permission-groups` / `pm list permissions -d` — listar grupos e permissoes
- `adb shell pm path <pkg>` — caminho do APK (pode ser split: base + split_config.*.apk)
- `adb shell pm dump <pkg>` — dump completo do pacote (permissoes, assinatura, servicios, activities)
- `adb shell pm clear <pkg>` — limpar dados e cache do app (factory reset do app)
- `adb shell pm grant <pkg> <permission>` — conceder permissao em runtime
- `adb shell pm revoke <pkg> <permission>` — revogar permissao
- `adb shell pm enable <component>` — habilitar componente (ex: receiver desativado)
- `adb shell pm disable <component>` — desabilitar componente
- `adb shell pm hide <pkg>` — esconder app (sem desinstalar, MIUI respeita)
- `adb shell pm unhide <pkg>` — reverter hide
- `adb shell pm uninstall --user 0 <pkg>` — desinstalar so do usuario (mantem pra re-enable)
- `adb shell pm install-create` / `install-write` / `install-commit` — sessao de instalacao incremental
- `adb shell pm trim-caches <size>` — limpar caches ate atingir tamanho
- `adb shell pm get-app-links <pkg>` — estado de app links verificados

### `cmd` — interface para servicos do sistema (Android 7+)
- `adb shell cmd activity` / `cmd package` / `cmd window` — alias para am/pm/wm
- `adb shell cmd statusbar expand-notifications` / `expand-settings` / `collapse`
- `adb shell cmd input <comando>` — alias do input
- `adb shell cmd notification list` — listar notificacoes ativas (Android 12+)
- `adb shell cmd notification remove -p <pkg>` — remover notificacoes de um app
- `adb shell cmd uimode night yes|no|auto` — forcar modo escuro on/off
- `adb shell cmd thermalservice` — servico termal
- `adb shell cmd jobscheduler` — listar jobs em fila

### Window Manager (wm) — tela
- `adb shell wm size` — resolucao atual (1080x2400)
- `adb shell wm density` — densidade atual (440)
- `adb shell wm size 720x1600` — sobrescrever resolucao (override)
- `adb shell wm density 480` — sobrescrever densidade
- `adb shell wm size reset` — voltar ao padrao
- `adb shell wm density reset`
- `adb shell wm overscan 0,0,0,0` — ajustar overscan (left,top,right,bottom)

### Settings (configuracoes persistidas)
- `adb shell settings get system|secure|global <key>` — ler valor
- `adb shell settings put system|secure|global <key> <value>` — alterar
- `adb shell settings delete system|secure|global <key>` — remover
- `adb shell settings list system|secure|global` — listar todos
- Comuns: `settings put global Development_Settings Enabled 1`, `settings put system screen_off_timeout 600000`
- `adb shell settings get global http_proxy` — proxy do sistema
- `adb shell settings put global http_proxy <ip:porta>` — configurar proxy

### Input completo (UI automation exaustivo)
- `adb shell input tap <x> <y>` — toque unico
- `adb shell input swipe <x1> <y1> <x2> <y2> [duration_ms]` — swipe; duracao default 300ms
- `adb shell input text "<string>"` — digitar (nao aceita espacos em alguns shells; use `%s`)
- `adb shell input keyevent <CODE>` — emular tecla; keycodes frequentes:
  - 3 = HOME, 4 = BACK, 5 = CALL, 6 = ENDCALL
  - 19/20/21/22 = UP/DOWN/LEFT/RIGHT (D-pad)
  - 23 = DPAD_CENTER, 24/25 = VOLUME_UP/DOWN
  - 26 = POWER, 27 = CAMERA, 66 = ENTER, 82 = MENU
  - 84 = SEARCH, 164 = MUTE, 220 = BRIGHTNESS_UP
  - 224 = WAKEUP, 223 = SLEEP
- `adb shell input draganddrop <x1> <y1> <x2> <y2> [speed]` — drag (Android 8+)
- `adb shell input roll <dx> <dy>` — roll trackball
- `adb shell input motionevent <action> <x> <y>` — evento motion customizado
- `adb shell uiautomator dump --compressed /sdcard/ui.xml` — dump comprimido
- `adb shell uiautomator events` — stream de eventos UI em tempo real

### dumpsys por servico — diagnostico profundo
- `adb shell dumpsys battery` — bateria (level, status, health, temp)
- `adb shell dumpsys battery set level 50` — forcar nivel (debug)
- `adb shell dumpsys battery reset` — desfazer forcas
- `adb shell dumpsys activity top` — activity no topo (foco)
- `adb shell dumpsys activity processes` — todos processos ativos
- `adb shell dumpsys window | findstr mFocusedApp` — app com foco
- `adb shell dumpsys notification` — todas notificacoes ativas
- `adb shell dumpsys notification --noredact` — incluindo texto privado
- `adb shell dumpsys power` — wake locks,.screen state
- `adb shell dumpsys wifi` — conexao wifi, scan results
- `adb shell dumpsys netstats` — uso de dados por app
- `adb shell dumpsys diskstats` — uso de disco por particao
- `adb shell dumpsys gfxinfo <pkg>` — info de renderizacao (jank, frames)
- `adb shell dumpsys meminfo <pkg>` — memoria do app em detalhe
- `adb shell dumpsys cpuinfo` — CPU por processo
- `adb shell dumpsys sensorservice` — sensores disponiveis
- `adb shell dumpsys media.camera` — cameras, resolucoes, modos
- `adb shell dumpsys bluetooth_manager` — estado bluetooth
- `adb shell dumpsys location` — ultima localizacao, providers
- `adb shell dumpsys alarm` — alarmes pendentes (cada app agenda)
- `adb shell dumpsys fm` — servico de radio FM (se presente)
- `adb shell dumpsys package <pkg> | findstr permission` — permissoes de um app
- `adb shell dumpsys appops` — operacoes revoltas a permissoes

### Backup e restore
- `adb backup -f <file.ab> [-noapk] <pkg>` — backup de app + dados (requer confirmacao na tela)
- `adb restore <file.ab>` — restaurar backup
- `adb shell bmgr backup <pkg>` — forcar backup via BackupManager
- `adb shell bmgr restore <pkg>` — forcar restore
- `adb shell bmgr run` — rodar jobs pendentes de backup

### Logcat avancado
- `adb logcat -d` — dump e sai
- `adb logcat -d *:E` — so erros (E, F = fatal, W = warning, I = info, D = debug, V = verbose)
- `adb logcat -d -v threadtime` — formato com timestamp e thread
- `adb logcat -d -v colored` — saida colorida
- `adb logcat --pid=<pid>` — so de um processo
- `adb logcat -s <tag>:<level>` — filtrar tag (ex: `-s ActivityManager:I`)
- `adb logcat -c` — limpar buffer
- `adb logcat -g` — mostra tamanho dos buffers
- `adb logcat -G 16M` — setar buffer pra 16MB
- `adb logcat -b all -d` — buffers: main, system, crash, radio, events
- `adb logcat -b crash -d` — so logs de crash

### Profiling e performance
- `adb shell cmd package compile -m everything <pkg>` — forcar AOT (compilacao completa)
- `adb shell cmd package compile --reset <pkg>` — limpar dados de profile
- `adb shell dumpsys gfxinfo <pkg> framestats` — latencia frame a frame
- `adb shell simpleperf record -a --duration 10 -o /sdcard/perf.data` — profiling nativo
- `adb shell logcat -Q` — logcat de quickboot
- `adb shell am profile start <pid> <file>` — iniciar profiling de um processo Java
- `adb shell am profile stop` — parar profiling

### MIUI especifico (Redmi Note 11, MIUI 14)
- Após `adb install`, dialog "Permitir" costuma aparecer (~3s) — coordenada tipica do Permitir: `adb shell input tap 800 1500`
- `adb shell settings put global development_settings_enabled 1` — habilitar opcoes dev
- `adb shell pm suppress <component>` pode nao funcionar igual AOSP (MIUI bloqueia)
- Para desativar otimizacao de bateria MIUI: vai em Config > Apps > VoxUmGrau > Bateria > Sem restricoes (nao tem caminho ADB confiavel)
- MIUI SafeMode: boot segurar volume up apos logo
- `adb shell cmd push_rule <pkg> <url_pattern> <path>` — regras de push MIUI (pode divergir)

### Fastboot (apos `adb reboot bootloader`)
- `fastboot devices` — listar (substitui adb no bootloader)
- `fastboot flash <partition> <img>` — flash de particao
- `fastboot oem unlock` / `fastboot flashing unlock` — desbloquear bootloader
- `fastboot reboot` — voltar ao sistema
- `fastboot reboot recovery` — ir ao recovery
- Fora do escopo agora, mas Jarvis sabe o caminho

### Padroes de automacao MIUI validados
1. **Tela bloqueada**: `adb shell input keyevent 224` (KEYCODE_WAKEUP) + `adb shell input swipe 540 1800 540 600 100` (desliza pra cima)
2. **Fechar dialog de permissao**: `adb shell input keyevent 4` (BACK) fecha dialog atual
3. **Screenshot + dump + OCR**: screencap → pull → uiautomator dump → parse → tap em coordenada
4. **Scroll determinado**: swipe 540 1800 540 400 400 (desce); swipe 540 400 540 1800 400 (sobe)
5. **Selecionar item em lista**: tap unico no elemento (apos dump encontrar bounds)

### Cenarios de uso futuros no ecossistema
- **Diagnostico BibliaEstudoCompleta**: rodar `am instrument` pra testes automatizados antes de commit
- **Build VoxUmGrau**: fluxo `build.ps1 -Install` ja usa `adb install -r`
- **Capturas do widget**: screencap para validar grafico no celular
- **Automacao de testes**: `am instrument -w com.voxumgrau.app.test/androidx.test.runner.AndroidJUnitRunner`
- **Limpeza de cache**: `pm clear com.biblia.estudo` reseta estado de testes

## Conexoes

- [[cluster-hub-programacao]]