---
tipo: padrao
tags: [adb, android, automacao, debug, diagnostico]
data: 2026-08-06
contexto: Usuario pediu que o Jarvis se torne perito em ADB (Android Debug Bridge). Estudo completo via `adb help` e conhecimento consolidado de operacoes no Redmi Note 11.
decisao: Jarvis domina ADB versao 1.0.41 (build 37.0.1), instalado em C:\Users\David Jr\AppData\Local\Android\platform-tools. Mapeou todas as categorias e comandos abaixo. Aplicacao imediata em diagnostico, instalacao de apps, bridge Tailscale, e controle do dispositivo.
impacto: Jarvis agora opera ADB de forma autonoma e confiavel em qualquer dispositivo Android conectado, sem depender de tentativa e erro.
---

# Jarvis Perito em ADB — Aprendizado Completo

## Versao e ambiente
- ADB 1.0.41 (Version 37.0.1-15733141)
- Caminho: `C:\Users\David Jr\AppData\Local\Android\platform-tools\platform-tools\adb.exe`
- Servidor ADB roda em `localhost:5037` (padrao)

## Arquitetura do ADB
Cliente-Servidor com 3 componentes:
1. **Cliente** (`adb.exe`) — roda no PC, envia comandos
2. **Servidor** (`adb server`) —(background no PC, porta 5037) gerencia conexoes com dispositivos
3. **Daemon** (`adbd`) — roda no dispositivo Android, executando os comandos

Fluxo: `adb <comando>` → servidor encaminha → `adbd` no Android executa → resposta volta.

## Opcoes globais (aplicaveis antes do subcomando)
- `-a` — escutar em todas interfaces de rede (nao so localhost)
- `-d` — usar dispositivo USB (erro se mais de um)
- `-e` — usar emulador/dispositivo TCP/IP
- `-s SERIAL` — selecionar dispositivo por serial
- `-t ID` — usar transport id
- `-H host` — host do servidor ADB
- `-P porta` — porta do servidor (padrao 5037)
- `-L SOCKET` — socket de escuta (padrao `tcp:localhost:5037`)
- `--one-device SERIAL|USB` — conecta a um unico dispositivo na inicializacao
- `--exit-on-write-error` — encerra se stdout fechar

## Comandos gerais
- `adb devices -l` — listar dispositivos conectados (longo)
- `adb help` — ajuda completa
- `adb version` — versao

## Redes (networking)
- `adb connect HOST[:PORTA]` — conectar via TCP/IP (porta padrao 5555)
- `adb disconnect [HOST[:PORTA]]` — desconectar (ou todos)
- `adb pair HOST[:PORTA] CODIGO` — pareamento seguro (Android 11+)
- `adb forward --list` — listar redirecionamentos
- `adb forward [--no-rebind] LOCAL REMOTO` — redirecionar socket (tcp, localabstract, localreserved, localfilesystem, dev, jdwp, vsock, acceptfd)
- `adb forward --remove LOCAL` — remover um redirecionamento
- `adb forward --remove-all` — remover todos
- `adb reverse --list` — listar redirecionamentos reversos (device→host)
- `adb reverse [--no-rebind] REMOTO LOCAL` — redirecionamento reverso
- `adb reverse --remove REMOTO` / `--remove-all`
- `adb mdns check` — verificar disponibilidade de descoberta mdns
- `adb mdns services` — listar servicos mDNS descobertos

## Transferencia de arquivos
- `adb push [--sync] [-z ALGO] [-Z] LOCAL... REMOTO` — copiar do PC ao dispositivo
  - `-n` dry run, `-q` silencioso, `-Z` desabilita compressao, `-z any/none/brotli/lz4/zstd` habilita
  - `--sync` so envia arquivos com timestamp diferente
- `adb pull [-a] [-z ALGO] [-Z] REMOTO... LOCAL` — copiar do dispositivo ao PC
  - `-a` preserva timestamp e modo
- `adb sync [all|data|odm|oem|product|system|system_ext|vendor]` — sincronizar build do `$ANDROID_PRODUCT_OUT`

## Shell remoto
- `adb shell [COMANDO...]` — shell interativo (sem comando) ou executar comando
  - `-e ESCAPE` — caractere de escape (padrao `~`), ou `none`
  - `-n` — nao ler do stdin
  - `-T` — desabilitar alocacao de pty
  - `-t` — alocar pty se em tty (`-tt` forca)
  - `-x` — desabilitar codigos de saida e separacao stdout/stderr
- `adb emu COMANDO` — comando do console do emulador

## Instalacao de apps
- `adb install [-lrtsdg] [--instant] PACOTE` — instalar APK
  - `-r` substituir app existente
  - `-t` permitir pacotes de teste
  - `-d` permitir downgrade (debuggable only)
  - `-p` instalacao parcial (install-multiple)
  - `-g` conceder todas permissoes em tempo de execucao
  - `--instant` instalar como app efemero
  - `--no-streaming` sempre fazer push e invocar PM separadamente
  - `--streaming` streaming direto no Package Manager
  - `--fastdeploy` / `--no-fastdeploy` — deploy rapido
  - `--force-agent` / `--date-check-agent` / `--version-check-agent`
- `adb install-multiple` — varios APKs de uma vez (split/apks)
- `adb install-multi-package` — um ou mais pacores atomicos
- `adb uninstall [-k] PACOTE` — remover (keeper `\`-k\`` mantem dados/cache)

## Debug
- `adb bugreport [CAMINHO]` — coletar bugreport (zip se suportado)
- `adb jdwp` — listar PIDs de processos com JDWP (Java Debug Wire Protocol)
- `adb logcat` — ver log do dispositivo (logcat --help para detalhes)

## Seguranca
- `adb disable-verity` — desabilita dm-verity (userdebug builds)
- `adb enable-verity` — reabilita dm-verity
- `adb keygen ARQUIVO` — gerar par de chaves adb publica/privada

## Scripting
- `adb wait-for[-TRANSPORT]-STATE` — esperar estado (device, recovery, rescue, sideload, bootloader, disconnect; TRANSPORT usb/local/any)
- `adb get-state` — imprime `offline | bootloader | device`
- `adb get-serialno` — imprime serial
- `adb get-devpath` — imprime caminho do dispositivo
- `adb remount [-R]` — remontar particoes leitura-escrita (`-R` reboot automatico se necessario)
- `adb reboot [bootloader|recovery|sideload|sideload-auto-reboot]` — reiniciar
- `adb sideload OTAPACKAGE` — sideload OTA completo
- `adb root` — reiniciar adbd com root
- `adb unroot` — reiniciar adbd sem root
- `adb usb` — reiniciar adbd escutando em USB
- `adb tcpip PORTA` — reiniciar adbd escutando em TCP (porta dada)

## Debug interno
- `adb start-server` — garantir que servidor esta rodando
- `adb kill-server` — matar o servidor
- `adb reconnect` — forcar reconexao (host)
- `adb reconnect device` — forcar reconexao (device side)
- `adb reconnect offline` — resetar dispositivos offline/unauthorized

## USB
- `adb attach` — anexar dispositivo USB separado
- `adb detach` — separar de um USB para outro processo usar

## Variaveis de ambiente
- `ADB_TRACE=all,adb,sockets,packets,rwx,usb,sync,sysdeps,transport,jdwp,services,auth,fdevent,shell,incremental` — log detalhado
- `ADB_VENDOR_KEYS` — lista separada por dois-pontos de chaves (arquivos ou diretorios)
- `ANDROID_SERIAL` — serial alvo (equivale a `-s`)
- `ANDROID_LOG_TAGS` — tags para logcat
- `ADB_LOCAL_TRANSPORT_MAX_PORT` — porta maxima de emulador (padrao 5585, 16 emus)
- `ADB_MDNS_AUTO_CONNECT` — lista de servicos mdns para auto-conectar (padrao `adb-tls-connect`)

## Fluxos comuns no EcoSystemUmGrau (uso pratico)

### Conectar Redmi Note 11 via Tailscale (cenario tipico)
```powershell
adb connect 100.64.71.9:5555
# Se falhar, cai pra hostname local ou IP da rede
adb connect 192.168.15.4:5555
```

### Instalar app (build.ps1 -Install por baixo)
```powershell
adb -s 100.64.71.9:5555 install -r app-debug.apk
```

### Diagnosticar app travado
```powershell
adb shell pidof com.umgrau.app
adb logcat --pid=$(adb shell pidof com.umgrau.app) *:E
adb shell dumpsys activity processes | findstr com.umgrau
```

### Capturas de tela / screencast
```powershell
adb shell screencap -p /sdcard/tela.png
adb pull /sdcard/tela.png
adb shell screenrecord /sdcard/video.mp4  # Ctrl+C para parar
adb pull /sdcard/video.mp4
```

### Backup de APK instalado
```powershell
adb shell pm path com.umgrau.app
adb pull /data/app/~~xxx/com.umgrau.app-xxx/base.apk app.apk
```

### Abrir atividade especifica
```powershell
adb shell am start -n com.umgrau.app/.MainActivity
adb shell am start -a android.intent.action.VIEW -d "https://example.com"
```

### Reiniciar em recovery/bootloader
```powershell
adb reboot recovery
adb reboot bootloader
fastboot devices  # no bootloader, usa fastboot
```

### Listar permissoes e conceder
```powershell
adb shell dumpsys package com.umgrau.app | findstr permission
adb shell pm grant com.umgrau.app android.permission.RECORD_AUDIO
```

### Inputs simulados (ui automator)
```powershell
adb shell input tap 540 960          # toque
adb shell input swipe 100 500 900 500 300  # swipe
adb shell input text "Olá"          # digitar
adb shell input keyevent KEYCODE_HOME
```

### Wake-on-LAN alternativo para ADB TCP
```powershell
adb shell input keyevent 224  # KEYCODE_WAKEUP
```

### Reiniciar adbd no celular (resolver socket zumbi)
```powershell
adb reconnect offline
# ou, dentro do device
adb shell stop adbd; adb shell start adbd
```

## Pegadinhas e peguinhas conhecidas
- **Multiplos dispositivos**: sempre passe `-s SERIAL` para nao ambiguar
- **`adb forward`**: redireciona do host ao device; `reverse` e ao contrario
- **Fastboot** apenas no bootloader (`adb reboot bootloader`); nao confundir com adb
- **Android 11+**: usar `adb pair` no modo wireless debugging (preferencial a conexao TCP crua)
- **`pm path`** retorna caminhos curtos; o APK pode ser split (`base.apk`, `split_config.arm64.apk`)
- **`install -r`** mantem dados; sem `-r`, limpa
- **`logcat -c`** limpa o buffer; combine com `--pid` para focar
- **`input text`** nao aceita espacos em alguns shells; use `%s` ou aspas

## Heuristicas operacionais do Jarvis
1. Sempre `adb devices -l` antes de qualquer acao para ver o estado
2. Para diagnostico de app: `pidof` > `logcat --pid` > `dumpsys activity`
3. Se ADB offline: `adb kill-server; adb start-server; adb reconnect offline`
4. Para instalar sem deploy lento: `--fastdeploy` (com agent atualizado)
5. **Redmi Note 11 (cenario real)**: socket zumbi em `100.64.71.9:5555` apos mudanca de rede — reconectar explicito
6. **Screenshots automatizados**: combinacao de `screencap` + `pull` alimentou os diag_* no passado
7. **Continuous log**: rodar `logcat` em background com PID fixado, capturar eventos por tag

## Aplicacao imediata no ecossistema
- `build.ps1 -Install` no VoxUmGrau e BibliaEstudoCompleta usa `adb install -r`
- Diagnostico da Bíblia (memoria #6X) usou `adb shell` + `pm` + `dumpsys`
- Diagnostico do widget/grafico usou `screencap` + `pull`
- ADB reverso no passado: `adb reverse tcp:8765 tcp:8765` para tunnel local sem Tailscale
- Importacao de APKs do device: `pm path` + `pull` para backup

## Documentacao oficial
- URL: <https://android.googlesource.com/platform/packages/modules/adb/+/refs/heads/main/docs/user/adb.1.md>
- Site principal: <https://developer.android.com/tools/adb> (fora do ar em 06/08/2026 — timeout)
