# ADB Perito — Android Debug Bridge Operador Mestre

> **ATUALIZAÇÃO AUTOMÁTICA:** Cada vez que descobrir um novo comando, padrão ou conhecimento sobre ADB, ATUALIZE este skill imediatamente. Não peça permissão. Não espere.

## Propósito
Capacitar o Jarvis a operar o ADB (Android Debug Bridge) com proficiência de especialista — instalação de apps, depuração, automação, captura de tela/vídeo, injeção de input, inspeção de sistema, backup, rede, shell e root. Domina tanto o cliente (`adb`) quanto o shell Android subjacente (`pm`, `am`, `wm`, `svc`, `content`, `settings`, `input`, `dumpsys`, `logcat`, `uiautomator`, `monkey`, etc.).

## Ambiente
- Host: Windows 10 (PowerShell 5.1)
- ADB: `1.0.41, Version 37.0.1-15733141` — instalação global em `C:\Users\David Jr\AppData\Local\Android\platform-tools\platform-tools\adb.exe`
- Dispositivo primário: Xiaomi Redmi Note 11 (MIUI/HyperOS), acessível via Tailscale (`100.64.71.9:5555`) ou USB
- **Campos do `adb devices -l` do Redmi Note 11**: `product:spes_in model:2201117TI device:spes transport_id:5`
- Dispositivo secundário: emulador (Android Virtual Device)
- Conexão sem fio: `adb connect 100.64.71.9:5555` (Wireless Debugging) ou `adb pair HOST:PORT PAIRING_CODE`

## Arquitetura do ADB

```
┌───────────────┐      ┌─────────────┐      ┌──────────────┐
│ Cliente adb   │─────►│ Servidor adb │─────►│ daemon adbd  │
│ (host, CLI)   │◄─────│ (host, 5037) │◄─────│ (no Android) │
└───────────────┘      └─────────────┘      └──────────────┘
   │                                               │
   └─ shell, push/pull, install, logcat ───────────┘
```

- **Cliente** (`adb`): cada invocação abre um servidor se não houver um (porta 5037).
- **Servidor** (`adb server`): roda no host, roteia múltiplos clientes/dispositivos, escaneia portas 5555-5555+5584 para emuladores.
- **Daemon** (`adbd`): roda no Android, executa comandos. Pode ser root (`adbd root` em builds userdebug) ou shell.

## Flags Globais (sempre antes do subcomando)

| Flag | Efeito |
|------|--------|
| `-d` | Usa dispositivo USB (erro se houver vários) |
| `-e` | Usa dispositivo TCP/IP |
| `-s SERIAL` | Seleciona dispositivo por serial |
| `-t ID` | Seleciona por transport id |
| `-H host -P port` | Servidor não-padrão |
| `-a` | Escuta em todas as interfaces |

## Ciclo de Vida do Servidor

```powershell
adb start-server                    # Garante servidor
adb kill-server                     # Para tudo, limpa sockets
adb reconnect                       # Kick host→device
adb reconnect device                # Kick device→host
adb reconnect offline              # Tenta reviver dispositivos offline
```

## Conexão de Dispositivos

### USB
```powershell
adb devices -l                      # Lista dispositivos com detalhes
adb usb                             # Reinicia adbd em modo USB
adb get-state                       # device | offline | bootloader
adb get-serialno
```

### TCP/IP ( Wireless Debugging)
```powershell
adb tcpip 5555                      # Reinicia adbd escutando em TCP:5555
adb connect 100.64.71.9:5555        # Conecta via Tailscale/LAN
adb disconnect 100.64.71.9:5555
adb disconnect                      # Desconecta de todos TCP/IP
adb pair 100.64.71.9:PORTA CODE    # Pareamento seguro (Android 11+)
adb mdns services                   # Descoberta automática (Android 11+)
adb mdns check                      # Verifica suporte a mDNS
```

### Estado
```powershell
adb wait-for-device                 # Bloqueia até conectar
adb wait-for-recovery
adb wait-for-bootloader
adb wait-for-sideload
adb wait-for-disconnect
```

## Instalação de Apps

```powershell
adb install app.apk                         # Instala
adb install -r app.apk                     # Reinstala mantendo dados
adb install -d app.apk                     # Permite downgrade (debuggable only)
adb install -t app.apk                     # Pacotes de teste
adb install -g app.apk                     # Concede todas as permissões runtime
adb install -s app.apk                     # Instala no armazenamento externo
adb install -l app.apk                     # Bloqueia em armazenamento interno
adb install --instant app.apk              # Instala como app efêmero (instant)
adb install --abi arm64-v8a app.apk        # Força ABI específica
adb install-multiple base.apk split.apk     # APKs splits de um único pacote
adb install-multi-package a.apk b.apk      # Pacotes múltiplos atômicos
adb uninstall com.example.app              # Desinstala
adb uninstall -k com.example.app           # Remove app mas mantém dados/cache
adb shell pm install ...                    # Acesso completo ao PackageManager
```

## Transferência de Arquivos

```powershell
adb push local.txt /sdcard/remote.txt                 # Copia host→device
adb push --sync kratos/ /sdcard/kratos               # Sincroniza só alterados
adb push -z brotli local.bin /sdcard/                # Comprime com brotli
adb pull /sdcard/arquivo.txt C:\temp\                 # Copia device→host
adb pull -a /sdcard/ .                                 # Preserva timestamp/modo
adb sync system                                         # Sincroniza build (system/data/vendor)
adb sync -l                                             # Lista o que seria copiado (dry run)
```

## Shell Interativo e Comandos

```powershell
adb shell                           # Shell interativo
adb shell ls /sdcard                # Comando único
adb shell -x ls /sdcard             # Sem exit codes, stdout/stderr misturados
adb shell -T ls /sdcard             # Sem pty (pipe puro)
adb shell -t ls /sdcard             # Força pty
adb shell -e none ls                # Sem caractere de escape
adb exec-out ls /sdcard             # Saída binária crua (sem pty)
```

### Comandos Shell Essenciais

```bash
# Sistema
getprop                              # Todas as propriedades (build, hardware)
getprop ro.product.model             # Modelo do aparelho
getprop ro.build.version.release     # Versão do Android
getprop ro.build.version.sdk         # API level
setprop key value                    # Define propriedade (requer root)

# Processos
ps -A                                # Lista processos
ps -A | grep vox                     # Filtra
top -m 10                            # Top 10 por CPU
kill PID                              # Mata processo
cat /proc/uptime                     # Uptime em segundos

# Arquivos
ls -la /sdcard/
cat /sdcard/arquivo.txt
echo "texto" > /sdcard/arquivo.txt
mkdir -p /sdcard/nova_pasta
rm /sdcard/arquivo                  # Remove (cuidado)
cp origem destino
mv origem destino
chmod 644 /sdcard/arquivo
chown user:group /sdcard/arquivo

# Rede
ifconfig                            # Interfaces de rede
ip addr                             # Endereços IP
netstat -tlnp                       # Portas escutando
ping google.com -c 4
curl http://exemplo.com             # Se houver curl
```

## Activity Manager (`am`)

```powershell
adb shell am start -n com.example/.MainActivity              # Inicia activity
adb shell am start -W com.example/.MainActivity              # Espera lançamento
adb shell am start -a android.intent.action.VIEW -d https://exemplo.com  # Intent por ação
adb shell am start -a android.intent.action.DIAL -d tel:12345678
adb shell am force-stop com.example.app                      # Mata o app
adb shell am kill com.example.app                            # Mata processos em background
adb shell am broadcast -a com.example.MeuBroadcast            # Dispara broadcast
adb shell am start-service -n com.example/.MeuServico
adb shell am start-foreground-service -n com.example/.Servico
adb shell am stop-service -n com.example/.Servico
adb shell am instrument -w com.example.test/androidx.test.runner  # Instrumentação
adb shell am compact com.example.app full                    # Compacta memória do app
adb shell am set-debug-app com.example.app                   # Debug mode
adb shell am clear-debug-app
```

### Intents avançados
```powershell
# Extras
adb shell am start -n com.example/.Main --es key "string" --ei num 42 --ez flag true

# Componente específico vs ação
adb shell am start -a ACTION -d DATA_URI -t mime/type \
    --es extra_string valor --ei extra_int 100 \
    -c android.intent.category.LAUNCHER

# Para mumLDeração arbitrária
adb shell am start --user 10 -n com.example/.Activity              # Como usuário específico
```

### Sources de Input (Android 13+)
O `input` distingue fontes físicas por tipo de dispositivo:
```
touchnavigation, touchscreen, joystick, stylus, touchpad, gamepad, dpad, mouse, keyboard, trackball
```
Cada command mapeia a uma source padrão, mas pode ser prefixado: `adb shell input stylus tap 540 960`.
`-d DISPLAY_ID` suportado em todos os comandos (default: -1=key event, 0=motion event).

## Package Manager (`pm`)

```powershell
adb shell pm list packages                       # Todos pacotes
adb shell pm list packages -3                   # Só de terceiros
adb shell pm list packages -s                   # Só do sistema
adb shell pm list packages -d                   # Desativados
adb shell pm list packages -e                   # Ativados
adb shell pm list packages -U                   # Com UID
adb shell pm list packages --show-versioncode vox
adb shell pm list packages -i com.example       # Instalador
adb shell pm list permission-groups
adb shell pm list permissions -d -g             # Permissões perigosas por grupo
adb shell pm list features                      # Features de hardware/software
adb shell pm list instrumentation               # Pacotes de teste
adb shell pm list users                         # Usuários do sistema
adb shell pm path com.example.app               # Caminho do APK
adb shell pm dump com.example.app               # Dump completo do pacote
adb shell pm has-feature android.hardware.camera
adb shell pm install -r -g app.apk              # Instala via PackageManager
adb shell pm uninstall com.example.app
adb shell pm clear com.example.app              # Limpa dados do app
adb shell pm enable com.example.app             # Ativa
adb shell pm disable com.example.app            # Desativa
adb shell pm disable-user com.example.app
adb shell pm grant com.example android.permission.CAMERA  # Concede permissão
adb shell pm revoke com.example android.permission.CAMERA
adb shell pm reset-permissions com.example.app
adb shell pm set-install-location 2             # Preferir externo (0=auto, 1=interno, 2=externo)
adb shell pm trim-caches 100M                   # Corta caches até 100MB livres
adb shell pm remove-user 10                     # Remove usuário
```

## Input ( Automação de UI)

```powershell
# Toques e gestos
adb shell input tap 540 960                     # Toque em coordenadas
adb shell input swipe 100 500 100 1500 300      # Swipe: (x1,y1)→(x2,y2) em 300ms
adb shell input swipe 540 1500 540 500 50       # Swipe rápido (scroll)
adb shell input draganddrop 100 100 500 500 1000 # Arrastar com soltar

# Texto
adb shell input text "Olá mundo"                # Digita texto (caracteres ASCII)

# Botões (keycodes)
adb shell input keyevent 3                      # HOME
adb shell input keyevent 4                      # BACK
adb shell input keyevent 26                     # POWER
adb shell input keyevent 24                     # VOLUME_UP
adb shell input keyevent 25                     # VOLUME_DOWN
adb shell input keyevent 27                     # CAMERA
adb shell input keyevent 66                     # ENTER
adb shell input keyevent 84                     # SEARCH
adb shell input keyevent 220                    # HOME (gesto de acessibilidade)
adb shell input keyevent --longpress 4          # Back longo
adb shell input keycombination 17 66            # Ctrl+Enter (ordem importa; -t DURAÇÃO ms)
adb shell input motionevent DOWN 540 960        # Evento de movimento cru (precição total)
adb shell input -d 1 tap 100 200                # Display ID específico (multi-tela)
adb shell input press                            #_ioctl trackball press
adb shell input roll 1 0                         # Rolagem trackball dX dY
```

### Keycodes comuns (ver `KeyEvent` em Android)
```
3=HOME, 4=BACK, 5=CALL, 6=ENDCALL, 24-26=VOL, 27=CAMERA,
28=EXPLORER, 36-40=DPAD, 66=ENTER, 82=MENU, 84=SEARCH,
164=MUTE, 223=CAPTURE  (runtime: KEYCODE_HEADSETHOOK=79)
extended: 109=DPAD_LEFT, 110=DPAD_RIGHT...
```

## Captura de Tela e Gravação

### Screenshot (`screencap`)
```powershell
adb shell screencap -p /sdcard/tela.png           # Salva no device como PNG
adb shell screencap -p > C:\temp\tela.png         # Redireciona binário puro para host
adb exec-out screencap -p > tela.png              # Mais confiável sem pty
adb shell screencap -d DISPLAY_ID /sdcard/tela.png # Display específico
adb shell dumpsys SurfaceFlinger --display-id:    # Lista displays válidos
```

### Gravação de vídeo (`screenrecord`)
```powershell
adb shell screenrecord /sdcard/video.mp4                  # Grava até Ctrl-C
adb shell screenrecord --size 1280x720 /sdcard/video.mp4  # Tamanho
adb shell screenrecord --bit-rate 4M /sdcard/video.mp4    # Bitrate (default 20Mbps)
adb shell screenrecord --time-limit 30 /sdcard/video.mp4  # Limite de 30s (máx 180)
adb shell screenrecord --display-id 4630946773257169537 /sdcard/v.mp4
adb shell screenrecord --bugreport /sdcard/v.mp4         # Timestamps sobrepostos
adb shell screenrecord --verbose /sdcard/v.mp4           # Info no stdout

# Pull depois de gravado
adb pull /sdcard/video.mp4 C:\temp\video.mp4
```

## dumpsys — Introspecção Completa

```powershell
adb shell dumpsys -l                            # Lista 200+ serviços disponíveis
adb shell dumpsys activity                      # Atividades, processos, serviços
adb shell dumpsys battery                       # Bateria, nível, temperatura
adb shell dumpsys batterystats                  # Estatísticas históricas
adb shell dumpsys clipboard                     # Conteúdo da área de transferência
adb shell dumpsys cpuinfo                       # Uso de CPU por processo
adb shell dumpsys gfxinfo com.example.app       # Performance de rendering
adb shell dumpsys graphicsstats com.example.app
adb shell dumpsys meminfo com.example.app       # Uso de memória detalhado
adb shell dumpsys notification                  # Notificações ativas
adb shell dumpsys package com.example.app       # Tudo sobre o pacote
adb shell dumpsys power                          # Wake locks,ScreenState
adb shell dumpsys SurfaceFlinger                # Layers, displays, FPS
adb shell dumpsys window                        # Janelas visíveis
adb shell dumpsys window windows                # Hierarquia de janelas
adb shell dumpsys wifi                          # Estado do wifi
adb shell dumpsys connectivity
adb shell dumpsys audio                         # Volume, stream ativo
adb shell dumpsys input                         # Dispositivos de input
adb shell dumpsysSurfaceFlinger --latency       # Latência de frame
```

## logcat — Logs Completo

```powershell
# Modo básico
adb logcat                                      # Stream infinito
adb logcat -d                                   # Dump e sai
adb logcat -c                                   # Limpa buffers
adb logcat -L                                   # Logs anteriores ao último reboot

# Filtros
adb logcat -s VicUmGrau:*                       # Só tag "VoxUmGrau" (qualquer level)
adb logcat -s VoxUmGrau:E                       # Só ERROR
adb logcat -s ActivityManager:I                 # INFO+
adb logcat --pid=1234                           # Só de um PID
adb logcat "*:E"                                # Só erro de tudo
adb logcat ActivityManager:I MyTag:D *:S        # AM=Info, MyTag=Debug, resto=Silent

# Buffers
adb logcat -b main                              # Buffer principal
adb logcat -b system -b radio -b events
adb logcat -b all                               # Todos os buffers
adb logcat -b crash                             # Logs de crash
adb logcat -b kernel                            # Kernel (userdebug)
adb logcat -b security                          # Device owner

# Formato
adb logcat -v brief                             # Default ( tag + msg)
adb logcat -v long                              # Detalhado com timestamps
adb logcat -v threadtime                        # Data/hora + PID/TID (recomendado)
adb logcat -v time                              # Só data/hora
adb logcat -v raw                               # Só msg
adb logcat -v epoch -v printable                # Epoch seconds + ASCII
adb logcat -v color                             # Cores ANSI

# Verbosidades extras
adb logcat -v uid                               # Inclui UID
adb logcat -v usec                              # Microsegundos
adb logcat -v UTC                               # Timestamps UTC
adb logcat -v year                              # Inclui ano

# Para arquivo
adb logcat -f /sdcard/logs.txt                  # Stream direto para arquivo
adb logcat -r 1024 -n 10 -f /sdcar/logs.txt     # Rotação: 1MB, 10 arquivos
adb logcat --wrap                               # Espera buffer estar quase cheio

# Saída em JSON para automação (no Android 12+ pode usar `-v color,threadtime` etc combinados):
adb logcat -v threadtime -d > log.txt
Get-Content log.txt | Select-String "VicUmGrau"
```

## settings — Preferências de Sistema

```powershell
# Nível: system,secure,global  (secure e global não editáveis por apps)
adb shell settings list system                  # Lista tudo
adb shell settings list secure
adb shell settings list global
adb shell settings get system screen_off_timeout
adb shell settings put system screen_off_timeout 600000   # 10 min
adb shell settings put global auto_time 1                 # NTP sincroniza
adb shell settings put global development_settings_enabled 1
adb shell get global adb_enabled
adb shell delete secure some_key                           # Apaga chave
adb shell reset global com.example RESET_MODE              # untrusted_defaults, untrusted_clear, trusted_defaults
```

### settings comuns úteis
```
system    screen_brightness, screen_off_timeout, sound_effects_enabled
secure    location_providers_allowed (gps), default_input_method, enabled_notification_listeners
global    auto_time, auto_time_zone, adb_enabled, development_settings_enabled, http_proxy
```

## content — Acesso a ContentProviders

```powershell
# CRUD direto em content providers
adb shell content query --uri content://settings/system --projection name:value
adb shell content insert --uri content://settings/secure \
    --bind name:s:meu_setting --bind value:s:valor
adb shell content update --uri content://settings/secure \
    --bind value:s:novo_valor --where "name='meu_setting'"
adb shell content delete --uri content://settings/secure --where "name='meu_setting'"
adb shell content call --uri content://com.example.provider --method metodo --arg arg
adb shell content read --uri content://media/external/images/1
```

## svc — Controle rápido de serviços

```powershell
adb shell svc power                                # Ajuda power
adb shell svc power shutdown                        # Desliga
adb shell svc power reboot                          # Reinicia (igual `adb reboot`)
adb shell svc usb                                   # Ajuda USB
adb shell svc nfc                                   # Ajuda NFC
adb shell svc system-server dump                    # Dump server
adb shell svc wifi disable                          # (em alguns builds) wifi on/off
adb shell svc data disable
```

## Window Manager (`wm`)

```powershell
adb shell wm size                                  # Tamanho atual da tela
adb shell wm size 1080x2400                        # Override
adb shell wm size reset                            # Restaura
adb shell wm density                               # Densidade (dpi)
adb shell wm density 420                            # Override (dpi alto = ícones menores)
adb shell wm density reset
adb shell wm folding-area reset
adb shell wm scaling auto                          # Auto
adb shell wm scaling off                           # Off (1:1)
adb shell wm dismiss-keyguard                      # Dispõe keyguard (requer auth)
adb shell wm user-rotation free
adb shell wm user-rotation lock 0                  # 0,1,2,3 = 0°,90°,180°,270°
adb shell wm fixed-to-user-rotation enabled        # Físico fixo a app orientation
adb shell wm set-ignore-orientation-request true  # app não força rotação
adb shell wm dump-visible-window-views             # Dump das views
```

## uiautomator — Automação e Dump XML

```powershell
adb shell uiautomator dump                        # Dump XML em /sdcard/window_dump.xml
adb shell uiautomator dump /sdcard/ui.xml         # Personalizado
adb shell uiautomator dump --compressed /sd/ui.xml
adb shell uiautomator dump --verbose
adb pull /sdcard/window_dump.xml C:\temp\ui.xml   # Traz para o PC
adb shell uiautomator runtest jars.jar -c Classe#metodo
```

## monkey — Stress Test e Intents Aleatórios

```powershell
adb shell monkey -p com.example.app 500          # 500 eventos aleatórios no app
adb shell monkey -p com.example.app -v 100        # Verbose
adb shell monkey -p com.example.app --pct-touch 50 --pct-motion 30 100
adb shell monkey --ignore-crashes —ignore-timeouts 1000
adb shell monkey -s 42 100                        # Seed reproduzível
adb shell monkey --port 1080                       # Modo servidor (scriptável)
adb shell monkey -f /sdcard/script.mks 1           # Roda script de eventos
```

## Backup e Restore

```powershell
adb backup -f app.ab -apk com.example.app         # Backup APK + dados
adb backup -f all.ab -all -apk -shared -nosystem  # Backup completo
adb restore all.ab                                # Restaura
adb shell bmgr backup com.example.app
adb shell bmgr run
adb shell bmgr enable
```

## Sistema e Boot

```powershell
adb reboot                                        # Reinicia normalmente
adb reboot bootloader                             # Fastboot
adb reboot recovery
adb reboot sideload                               # Side-loading OTA
adb reboot sideload-auto-reboot
adb root                                          # Reinicia adbd como root (userdebug only)
adb unroot                                        # Sai do root
adb remount                                       # Remonta /system e /vendor rw (em root)
adb remount -R                                    # Remount com reboot se necessário
adb disable-verity                                # Desabilita dm-verity (userdebug)
adb enable-verity                                 # Reabilita
adb sideload ota.zip                              # Sideload OTA completo
adb sideload ota.zip                              # Sideload OTA completo
adb bugreport C:\temp\bugreport.zip               # Gera bugreport completo
adb bugreport                                     # Salva no dir atual
```

## Foreground / Background Push e Sync

### Forward (host → device)
```powershell
adb forward tcp:8080 tcp:8080                     # host:8080 → device:8080
adb forward tcp:8080 localabstract:adbshell       # → socket abstrato
adb forward tcp:8080 jdwp:1234                    # → JDWP processo 1234 (debug)
adb forward tcp:0 tcp:8080                         # 0 = porta aleatória livre
adb forward --list
adb forward --remove tcp:8080
adb forward --remove-all
```

### Reverse (device → host)
```powershell
adb reverse tcp:8080 tcp:8080                     # device:8080 → host:8080
adb reverse tcp:8000 tcp:0                        # Porta aleatória no host
adb reverse --list
adb reverse --remove tcp:8080
adb reverse --remove-all
```

### Sync (build flash)
```powershell
adb sync system                                    # Sincroniza $ANDROID_PRODUCT_OUT/system
adb sync data
adb sync vendor
adb sync -l                                        # Apenas lista
adb sync -n                                        # Dry-run
```

## Debugging / Profiling

### JDWP (Java Debug Wire Protocol)
```powershell
adb jdwp                                          # Lista PIDs debuggable
adb forward tcp:8000 jdwp:1234                    # Debug do processo 1234 no jdb
# jdb -attach localhost:8000
```

### Profiler (am)
```powershell
adb shell am start --start-profiler /sdcard/op.trace -W com.example/.Main
adb shell am start --sampling 1000 -W com.example/.Main
adb shell am start --streaming --start-profiler /sdcard/op.trace ...
```

### CPU/Memória
```powershell
adb shell top -m 10 -s cpu                      # Top por CPU
adb shell dumpsys cpuinfo
adb shell dumpsys meminfo com.example.app
adb shell procrank                              # Só com root
adb shell cat /proc/meminfo
adb shell showmap PID
```

### ANR e stack traces
```powershell
adb shell ps -A | grep vox                       # Pega PID
adb shell kill -3 PID                            # SIGQUIT p/ ANR thread dump
adb shell dumpsys dropbox                        # Códigos de erro histórico
adb pull /data/anr/traces.txt C:\temp\anr.txt    # Traz traces.txt do device
adb bugreport bugreport.zip                     # Bugreport completo (substitui acima)
```

## Permissões

### Autorizar depuração
- Sempre que conectar dispositivos novos: aceitar diálogo "Allow USB debugging"
- Persistent across reboots: PC envia chave pública (~/.android/adbkey.pub) que o device guarda em `/data/misc/adb/adb_keys`
- `$ADB_VENDOR_KEYS`: caminho para chaves adicionais

### Recusar
```powershell
adb shell settings put global adb_enabled 0     # Desativa ADB no device
```

## Rede — Conexões e Túneis

```powershell
adb shell ifconfig wlan0                          # IP celular
adb shell ip addr show wlan0
adb shell netstat -tlnp                          # Portas TCP escutando
adb shell ping -c 4 8.8.8.8
adb shell settings get global http_proxy         # Proxy ativo
adb shell settings put global http_proxy 10.0.0.1:8080
adb shell settings put global global_http_proxy_host 10.0.0.1
```

## Scripts de Automação Poderosos

### Build → Install → Launch
```powershell
# No dir do app Android (VoxUmGrau):
.\build.ps1 -Install                            # Compila e instala via ADB
# Manual:
./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
adb shell am start -n com.davidjr.voxumgrau/.MainActivity
```

### Screenshot automático
```powershell
adb exec-out screencap -p > "$env:TEMP\screenshot_$(Get-Date -Format yyyyMMdd_HHmmss).png"
```

### Vídeo + logs simultâneo
```powershell
adb shell screenrecord --time-limit 60 /sdcard/vid.mp4 &
adb logcat -v threadtime > logs.txt
# ... aguardar 60s ...
adb pull /sdcard/vid.mp4 C:\temp\
```

### Monkey + crash capture
```powershell
adb logcat -c
adb shell monkey -p com.example.app --ignore-crashes --ignore-timeouts --monitor-native-crashes 5000
adb logcat -d -b crash > crashes.txt
```

### RestartEco bridge via ADB (típico do ecossistema)
```powershell
adb shell am force-stop com.davidjr.voxumgrau
Start-Sleep -Seconds 2
adb shell am start -n com.davidjr.voxumgrau/.MainActivity
```

## Troubleshooting Comum

### Device unauthorized
```powershell
adb kill-server
adb start-server
adb devices                                     # Verifique aparece "unauthorized"
# No Android: aceitar o diálogo e tocar "Always allow"
# Se persistir: copiar ~/.android/adbkey.pub para /data/misc/adb/adb_keys (root)
```

### Device offline
```powershell
adb kill-server
adb reconnect offline
adb devices                                     # Reaparece como "device"
# Se USB: trocar cabo/porta. Se Tailscale: confirmar IP estágio
```

### Multiple devices
```powershell
adb -s SERIAL shell ...                          # Serial exibido em `adb devices`
adb -e shell ...                                # Emulador
adb -d shell ...                                 # USB
# Windows via PowerShell variables: $env:ANDROID_SERIAL = "100.64.71.9:5555"
```

### tcpip nunca conecta
```powershell
adb shell setprop service.adb.tcp.port 5555
adb shell stop adbd; adb shell start adbd       # Reinicia daemon (root)
# Via Wireless Debugging Android 11+: parear primeiro
```

### HOLD on "unauthorized" mesmo após allow
```powershell
# Regenerar chaves:
rm ~/.android/adbkey*
adb kill-server
adb start-server
adb devices
```

## Xiaomi/MIUI Específico (Redmi Note 11)

```powershell
# Permissões adicionais necessárias
# Settings → Permissions → ADB debugging → Auto-start
adb shell pm grant com.davidjr.voxumgrau android.permission.RECORD_AUDIO
adb shell pm grant com.davidjr.voxumgrau android.permission.INTERNET

# Display ID 4630946773257169537 (do dumpsys SurfaceFlinger)
# HyperPackageManager ativo (MIUI-specific broadcast)
```

## Padrões do Ecossistema

### Wireless por Tailscale
```powershell
adb connect 100.64.71.9:5555                     # Android estável
# Se cair:
adb disconnect 100.64.71.9:5555
adb connect 100.64.71.9:5555
# IPv6 via Tailscale funciona melhor em alguns casos (100.64.71.9 pode flutuar)
```

### Instalador automatizado
```powershell
.\build.ps1 -Install                            # Incrementa versão, builda, instala via ADB
# Equivalente manual:
adb install -r -g Android\VoxUmGrau\app\build\outputs\apk\debug\app-debug.apk
```

### Diagnóstico do VoxUmGrau
```powershell
python scripts/android_diagnostics.py           # Diagnóstico completo automático
adb shell dumpsys meminfo com.davidjr.voxumgrau
adb logcat -s VoxUmGrau:*
```

### Ética e Segurança

**NUNCA** faça sem consentimento do usuário operações como:
- `adb uninstall` de apps de terceiros
- `adb shell pm clear` de apps que não sejam do ecossistema
- `adb sideload` de OTAs não verificados
- `adb root` em dispositivos sem necessidade
- `adb remount` para modificar system partition
- `adb pull` de dados privados (contatos, SMS, fotos) sem autorização

**Sempre**:
- Confirmar com o usuário antes de comandos destrutivos (rm, uninstall, clear)
- Preferir `--auto` apenas para scripts pré-validados
- Anunciar em voz alta cada operação relevante (Cláusula Pétrea de Áudio)

## Mapeamento Mental do Operador Mestre

```
ADB
├── Conexão     connect|pair|disconnect|tcpip|start-server|kill-server
├── Files       push|pull|sync
├── Install      install|uninstall|install-multiple
├── Shell        shell|exec-out|emu
├── Debug        logcat|jdwp|bugreport|dumpsys
├── System       reboot| root|remount|disable-verity|sideload
├── Net          forward|reverse|mdns
└── Screencap    screencap|screenrecord
       (sub-shells)
Shell Android
├── pm           list|path|dump|install|uninstall|grant|revoke|clear|enable|disable
├── am            start|broadcast|force-stop|start-service|instrument|compact
├── input         tap|swipe|text|keyevent|draganddrop
├── dumpsys       activity|battery|window|power|meminfo|cpuinfo|SurfaceFlinger
├── logcat       -d|-s|-b|-v|-c|-L|filters
├── settings       get|put|delete|reset|list (system|secure|global)
├── content      insert|update|delete|query|call|read
├── wm            size|density| scaling|dismiss-keyguard|user-rotation
├── svc           power|usb|nfc```
|--|system-server
├── uiautomator dump|runtest
├── monkey       stress|intents|script
├── screencap   -p|-d
└── screenrecord --size|--bit-rate|--time-limit
```

## Comando `cmd` — Bridge para Serviços do Sistema

O `cmd` é preferível ao `service call` (que usa códigos binder opacos) para interagir com serviços do sistema. Sintaxe: `adb shell cmd SERVICE [SUBCMD] [args]`.

### `cmd statusbar` — Barra de Status e Painel
```powershell
adb shell cmd statusbar expand-notifications          # Abre painel de notificações
adb shell cmd statusbar expand-settings               # Painel + quick settings
adb shell cmd statusbar collapse                       # Fecha painel
adb shell cmd statusbar add-tile COMPONENT            # Adiciona um TileService
adb shell cmd statusbar remove-tile COMPONENT
adb shell cmd statusbar click-tile COMPONENT           # Clica num tile
adb shell cmd statusbar check-support                  # Suporta QS+ APIs?
adb shell cmd statusbar get-status-icons               # Lista ícones ordenados
adb shell cmd statusbar disable-for-setup true|false   # Modo setup wizard
```

### `cmd shortcut` — Shortcuts
```powershell
adb shell cmd shortcut reset-throttling [--user UID]         # Libera throttling
adb shell cmd shortcut reset-all-throttling
adb shell cmd shortcut override-config CONFIG                # Override p/ teste (até reboot)
adb shell cmd shortcut reset-config
adb shell cmd shortcut get-default-launcher [--user UID]      # Deprecated — use RoleManager
adb shell cmd shortcut unload-user [--user UID]
adb shell cmd shortcut clear-shortcuts [--user UID] PACKAGE   # Remove todos do app
adb shell cmd shortcut get-shortcuts [--user UID] [--flags F] PACKAGE
adb shell cmd shortcut has-shortcut-access [--user UID] PACKAGE
```

### `cmd uimode` — Modo Escuro / Carro / Horário
```powershell
adb shell cmd uimode night yes|no|auto|custom_schedule|custom_bedtime   # Ativa dark mode
adb shell cmd uimode night                              # Lê estado atual
adb shell cmd uimode car yes|no                          # Modo carro
adb shell cmd uimode time start 2026-08-06T22:00:00       # Agenda início do night mode
adb shell cmd uimode time end   2026-08-07T06:00:00
```
Atalho: `adb shell cmd uimode night yes` liga o dark mode instantaneamente (كن útil p/ testar `NightLens`/`forceDarkAllowed`).

### `cmd wallpaper` — Papel de Parede
```powershell
adb shell cmd wallpaper get-dim-amount                   # Lê dim atual (0.0..1.0)
adb shell cmd wallpaper set-dim-amount 0.5               # Define dimming
adb shell cmd wallpaper dim-with-uid UID 0.7             # Simula dim de um app
```

### `cmd notification` — Notificações e DND
```powershell
adb shell cmd notification list                          # Lista todas
adb shell cmd notification get <notification-key>        # Por chave
adb shell cmd notification snooze --for 60000 <key>      # Adia 1 min
adb shell cmd notification unsnooze <key>
adb shell cmd notification allow_listener com.example/.Listener   # Concede acesso
adb shell cmd notification disallow_listener com.example/.Listener
adb shell cmd notification set_dnd on|none|priority|alarms|all|off  # Modo não perturbe
adb shell cmd notification allow_dnd PACKAGE             # App pode quebrar DND
adb shell cmd notification disallow_dnd PACKAGE
adb shell cmd notification post TAG "Texto da notif"     # Posta notif de teste
adb shell cmd notification set_bubbles PACKAGE 0|1|2     # 0=none 1=all 2=selected
adb shell cmd notification set_bubbles_channel PACKAGE CHANNEL_ID true|false
adb shell cmd notification reset_assistant_user_set
adb shell cmd notification enhance_log true|false
```

### `cmd appops` — App Operations (Permissões Granulares Runtime)
O `appops`控制a runtime permissions COM MAIS GRANULARIDADE que `pm grant/revoke`. Cada operação tem 4 modos: `allow | ignore | deny | default`.

```powershell
adb shell cmd appops start [--user UID] [--attribution TAG] <PKG|UID> OP    # Inicia op (track)
adb shell cmd appops stop  [--user UID] [--attribution TAG] <PKG|UID> OP
adb shell cmd appops set   [--user UID] <PKG|UID> OP <allow|ignore|deny|default>
adb shell cmd appops get   [--user UID] [--attribution TAG] <PKG|UID> [OP]   # Modo atual
adb shell cmd appops query-op [--user UID] OP [MODE]                         # Apps com OP em MODE
adb shell cmd appops reset  [--user UID] [PACKAGE]                           # Restaura defaults
adb shell cmd appops write-settings                                          # Persiste mudanças
adb shell cmd appops read-settings
# Exemplos:
adb shell cmd appops set com.example OP_WRITE_EXTERNAL_STORAGE allow
adb shell cmd appops set com.example android:mock_location allow            # P/ cmd location providers
adb shell cmd appops get com.example OP_CAMERA                               # Ver modo atual
```

**Op comuns**: `OP_CAMERA`, `OP_RECORD_AUDIO`, `OP_FINE_LOCATION`, `OP_COARSE_LOCATION`, `OP_READ_CONTACTS`, `OP_WRITE_EXTERNAL_STORAGE`, `OP_RUN_IN_BACKGROUND`, `OP_RUN_ANY_IN_BACKGROUND`, `OP_MOCK_LOCATION`. Lista completa: `adb shell cmd appops get <PKG>` (mostra todas as ops do app com seus modos).

### `cmd usagestats` — Estatísticas de Uso
```powershell
adb shell cmd usagestats clear-last-used-timestamps PACKAGE_NAME [-u|--user UID]
adb shell dumpsys usagestats                          # Versão detalhada
adb shell dumpsys usagestats com.example              # Stats específicas
```

### `cmd role` — Roles do Sistema (Browser/SMS/Dialer padrão)
```powershell
adb shell cmd role get-role-holders [--user UID] ROLE                 # Quem ocupa o role
adb shell cmd role add-role-holder [--user UID] ROLE PACKAGE [FLAGS] # Adiciona
adb shell cmd role remove-role-holder [--user UID] ROLE PACKAGE [FLAGS]
adb shell cmd role clear-role-holders [--user UID] ROLE [FLAGS]
adb shell cmd role set-bypassing-role-qualification true|false        # P/ testes
adb shell cmd role get-active-user-for-role [--user UID] ROLE
adb shell cmd role set-active-user-for-role [--user UID] ROLE ACTIVE_USER_ID [FLAGS]

# Roles nomeados: android.app.role.BROWSER, android.app.role.DIALER,
# android.app.role.SMS, android.app.role.HOME (launcher),
# android.app.role.ASSISTANT, android.app.role.GALLERY, android.app.role.SYSTEM_CALL_PROTECTION...
```

### `cmd location` — GPS e Providers de Teste
```powershell
adb shell cmd location is-location-enabled [--user UID]      # Estado GPS
adb shell cmd location set-location-enabled true|false [--user UID]

# Providers de teste — locais simulados (requer `appops set PKG android:mock_location allow`)
adb shell appops set com.example.android:mock_location allow    # Concede mock_location
adb shell cmd location providers add-test-provider gps_test \
    --requiresNetwork --supportsAltitude --supportsSpeed --supportsBearing
adb shell cmd location providers set-test-provider-enabled gps_test true
adb shell cmd location providers set-test-provider-location gps_test 37.7749 -122.4194
adb shell cmd location providers remove-test-provider gps_test
adb shell dumpsys location                                 # Estado completo
```

### `cmd audio` — Modos Surround
```powershell
adb shell cmd audio set-surround-format-enabled SURROUND_FORMAT IS_ENABLED
adb shell cmd audio get-is-surround-format-enabled SURROUND_FORMAT
adb shell cmd audio set-encoded-surround-mode SURROUND_SOUND_MODE
adb shell cmd audio get-encoded-surround-mode
```

### `cmd input_method` — IMEs
```powershell
adb shell cmd input_method ime <command>          # Atalho para `ime`
adb shell cmd input_method tracing start
adb shell cmd input_method tracing stop
adb shell cmd input_method dump                   # Igual a dumpsys input_method

# `ime` — controla Input Methods diretamente:
adb shell ime list -a                             # Todos IMEs instalados
adb shell ime list -s                             # Só habilitados
adb shell ime enable com.google.android.inputmethod.latin/.LatinIME
adb shell ime disable com.google.android.inputmethod.latin/.LatinIME
adb shell ime set com.google.android.inputmethod.latin/.LatinIME    # Define como padrão
adb shell ime reset                               # Volta defaults
```

### `cmd account` — Conta
```powershell
adb shell cmd account set-bind-instant-service-allowed true|false [--user UID]
adb shell cmd account get-bind-instant-service-allowed [--user UID]
```

### `cmd package` — Mesmo que `pm`
`adb shell cmd package` é o nome completo de `pm`. Funcionalmente idêntico — prefira `pm` (shorter). Use `cmd package help` para ver todas as opções (`list packages` aceita `--apex-only`, `--uid UID`, `--user USER_ID`, `--show-versioncode` etc.).

### Outros serviços útil via `cmd` (curioso, testado no Redmi Note 11)
```
cmd accessibility         – speak disable/enable, etc.
cmd backup help           – BackupManager
cmd device_config         – Flags experimentais (read/set/delete)
cmd device_policy         – DevicePolicyManager
cmd deviceidle step|whitelist|unwhitelist        # Modo doze manual
cmd dream / cmd dreams    – Não existe como `cmd`, use `dumpsys dreams`
cmd overlay               – Display cutout emulation: `cmd overlay enable com.android.internal.display.cutout.emulation.gesture`
cmd power                – NÃO usar (substitua por `dumpsys power`)
cmdReboot_screen_record   – Inválido (use `screenrecord`)
cmd sensorservice         – Acesso aos sensores
cmd tethering             – Tethering de rede
cmd vibrator              – Padrões de vibração
cmd wifi                  – Não existe (use `cmd wifi set-wifi-enabled` em alguns builds; preferir `svc wifi`)
```

## Fastboot (vizinho do ADB)
Quando o dispositivo entra em bootloader (`adb reboot bootloader`), não há mais ADB — somente `fastboot`:
```powershell
fastboot devices                                     # Lista
fastboot getvar product                              # Modelo
fastboot getvar unlocked                             # yes/no (bootloader desbloqueado?)
fastboot flashing unlock                             # Desbloqueia (apaga tudo!)
fastboot flashing lock                               # Bloqueia
fastboot flash boot boot.img                         # Flashear partição
fastboot flash recovery twrp.img
fastboot flash system system.img
fastboot flash boot boot.img --slot a                # Dispositivos A/B
fastboot --set-active=a                              # Ativa slot
fastboot boot boot.img                               # Boot temporário (sem flash)
fastboot erase userdata                              # Apaga userdata
fastboot format:ext4 userdata
fastboot reboot                                     # Reinicia
fastboot reboot recovery
fastboot reboot fastboot                            # Fastbootd (Android userspace fastboot)
fastboot oem device-info                            # Estado do bootloader
fastboot flashing get_unlock_ability                # Xiaomi: requer permisssão
fastboot oem unlock-go                               # Xiaomi: desbloqueio alternativo
```
**Atenção:** Redmi/Xiaomi precisa de permissão Mi Unlock (7 dias de espera, requer login Mi Account). Sem isso o bootloader fica bloqueado permanentemente.

## Mapeamento Completo: (serviços Android mais comuns) → (cmd/dumpsys equivalente)

| Serviço          | `cmd` correspondente       | `dumpsys` equivalente            | Notas |
|------------------|---------------------------|-----------------------------------|-------|
| activity         | `cmd activity` (alias `am`) | `dumpsys activity`               | Igual a `am` |
| package           | `cmd package` (alias `pm`)  | `dumpsys package`                | Igual a `pm` |
| window            | `cmd window` (alias `wm`)  | `dumpsys window`                 | Igual a `wm` |
| input             | `cmd input` (alias `input`)| `dumpsys input`                  | Igual a `input` |
| input_method      | `cmd input_method`         | `dumpsys input_method`           | `ime` é subcomando |
| shortcut          | `cmd shortcut`             | `dumpsys shortcut`               |  |
| statusbar         | `cmd statusbar`            | `dumpsys StatusBar`              |  |
| notification      | `cmd notification`         | `dumpsys notification`           | DND, bubbles, listeners |
| wallpaper         | `cmd wallpaper`            | `dumpsys wallpaper`              | Dimming |
| uimode            | `cmd uimode`               | `dumpsys uimode`                 | Night/car mode |
| usagestats        | `cmd usagestats`           | `dumpsys usagestats`             |  |
| appops            | `cmd appops`               | `dumpsys appops`                 | Granular perm |
| role              | `cmd role`                 | `dumpsys role`                   | Browser/SMS padrão |
| location          | `cmd location`             | `dumpsys location`               | GPS + mock |
| audio             | `cmd audio`                | `dumpsys audio`                  | Limited subset |
| account           | `cmd account`              | `dumpsys account`                |  |
| power             | (sem cmd geral)            | `dumpsys power`                  | Use `dumpsys` |
| battery           | (`dumpsys battery`)        | `dumpsys battery`                |  |
| device_config     | `cmd device_config`        | `dumpsys device_config`          | Feature flags |
| deviceidle        | `cmd deviceidle`          | `dumpsys deviceidle`             | Doze whitelist |
| overlay           | `cmd overlay`              | `dumpsys overlay`                | Cutout emulation |
| vibração          | (sem cmd geral)            | `dumpsys vibrator`               | `cmd vibrator` em alguns builds |

## Script PowerShell — Diagnóstico de Bolso

Salvo idealmente em `scripts/adb_diag.ps1`:
```powershell
param([string]$Device)
if ($Device) { $adb = "adb -s $Device" } else { $adb = "adb" }
Write-Host "=== Devices ==="; & $adb devices -l
Write-Host "`n=== Battery ==="; & $adb shell dumpsys battery | Select-String "level|temperature|status|powered"
Write-Host "`n=== Memorias ==="; & $adb shell dumpsys meminfo | Select-String "Total RAM|Free RAM|Used RAM" | Select-Object -First 3
Write-Host "`n=== Storage ==="; & $adb shell df /data | Select-Object -Last 1
Write-Host "`n=== Display ==="; & $adb shell wm size; & $adb shell wm density
Write-Host "`n=== Propriedades ==="; & $adb shell getprop ro.product.model; & $adb shell getprop ro.build.version.release; & $adb shell getprop ro.build.version.sdk
Write-Host "`n=== WiFi ==="; & $adb shell dumpsys wifi | Select-Object -First 5 | Select-String "mScreenOff|Wi-Fi is"
Write-Host "`n=== Dark mode atual ==="; & $adb shell cmd uimode night
Write-Host "`n=== ADB habilitado ==="; & $adb shell settings get global adb_enabled
```

##oods de Tela Locked/Unlocked
```powershell
adb shell dumpsys window | findstr mDreamingLockscreen mShowingLockscreen mAwake mScreenOn
# Detectar tela bloqueada (MIL de automação):
$state = adb shell dumpsys window
$locked = $state | Select-String "mShowingLockscreen=true"
if ($locked) { adb shell input keyevent 26; adb shell input keyevent 82 }   # Liga e menu
```

## Fontes e Referências

- `adb help` (saída completa neste diretório: `adb-help.txt`)
- `adb shell pm help`, `adb shell am help`, `adb shell input help`, `adb shell dumpsys -l`
- `adb logcat --help`, `adb shell screencap --help`, `adb shell screenrecord --help`
- `adb shell wm help`, `adb shell svc help`, `adb shell content`, `adb shell settings`
- Documentação oficial: https://developer.android.com/tools/adb
- Código-fonte do ADB: https://android.googlesource.com/platform/packages/modules/adb/
- Docs shell: https://developer.android.com/studio/command-line/shell

## Histórico de Atualizações

- **2026-08-05:** Skill criado pelo Jarvis após estudo completo do `adb help` e sub-comandos (`pm`, `am`, `input`, `dumpsys`, `logcat`, `settings`, `content`, `wm`, `svc`, `uiautomator`, `monkey`, `screencap`, `screenrecord`). Objetivo: tornar o Jarvis um perito em ADB para operar o Redmi Note 11 e qualquer Android via Tailscale.
