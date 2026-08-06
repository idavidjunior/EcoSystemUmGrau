---
tipo: padrao
tags: [adb, android, debug, bridge, ferramentas, expertise]
data: 2026-08-06
contexto: Aprendizado completo de ADB (Android Debug Bridge) para tornar o Jarvis um perito operador desta ferramenta
decisao: Criar base de conhecimento completa de ADB no ecossistema
impacto: Jarvis passa a ter domínio total de ADB para diagnóstico, instalação, depuração e automação Android
---

# ADB (Android Debug Bridge) — Domínio Completo

## O que é ADB

**Android Debug Bridge** é uma ferramenta de linha de comando versátil que permite comunicação bidirecional com dispositivos Android. É um programa **cliente-servidor** com três componentes:

1. **Cliente** — roda na máquina de desenvolvimento, envia comandos (`adb` no terminal)
2. **Daemon (adbd)** — roda no dispositivo Android em background, executa comandos
3. **Servidor** — roda na máquina de desenvolvimento em background, gerencia comunicação cliente↔daemon

## Arquitetura e Funcionamento

```
Máquina Host (PC)                    Dispositivo Android
┌─────────────────────┐              ┌─────────────────────┐
│  Cliente ADB        │◄────────────►│  Daemon (adbd)      │
│  (seu terminal)     │   TCP/USB    │  (background)       │
└─────────▲───────────┘              └─────────────────────┘
          │
          ▼
┌─────────────────────┐
│  Servidor ADB       │
│  (background,       │
│   porta 5037)       │
└─────────────────────┘
```

- **Porta padrão do servidor:** 5037 (localhost)
- **Porta padrão do daemon TCP:** 5555
- **Protocolo:** ADB protocol (binário, sobre USB ou TCP/IP)

## Comandos Fundamentais

### Gestão de Dispositivos
```bash
adb devices                    # Lista dispositivos conectados
adb devices -l                 # Lista com detalhes (modelo, transporte)
adb get-state                  # Estado: device | offline | bootloader | recovery
adb get-serialno               # Número de série do dispositivo
adb get-devpath                # Caminho do dispositivo USB
adb wait-for-device            # Espera dispositivo conectar
adb wait-for [-TRANSPORT] -STATE...  # Espera estado específico
```

### Direcionamento de Comandos (múltiplos dispositivos)
```bash
adb -d <cmd>                   # Único dispositivo USB
adb -e <cmd>                   # Único emulador rodando
adb -s <serial> <cmd>          # Dispositivo específico por serial
```

### Servidor ADB
```bash
adb start-server               # Inicia servidor (auto-inicia no primeiro comando)
adb kill-server                # Mata servidor (útil para resetar conexões travadas)
adb reconnect                  # Força reconexão host-side
adb reconnect device           # Força reconexão device-side
adb reconnect offline          # Reset dispositivos offline/unauthorized
```

### Conexão TCP/IP (Wireless)
```bash
adb tcpip 5555                 # Reinicia adbd no dispositivo ouvindo TCP porta 5555
adb connect IP[:5555]          # Conecta a dispositivo via TCP/IP
adb disconnect [IP[:5555]]     # Desconecta dispositivo TCP (ou todos)
adb pair IP[:PORT] [CODE]      # Emparelhamento seguro (Android 11+)
```

### Instalação de Apps
```bash
adb install [-lrtsdg] [--instant] <apk>           # Instala APK único
adb install-multiple [-lrtsdpg] [--instant] <apks> # Múltiplos APKs (split APKs)
adb install-multi-package [-lrtsdpg] [--instant] <apks> # Múltiplos pacotes atomicamente

# Flags principais:
# -r  Reinstalar mantendo dados
# -t  Permitir APKs de teste
# -d  Permitir downgrade de versionCode
# -g  Conceder todas permissões do manifest
# -s  Instalar no SD card
# --fastdeploy  Atualização rápida (só partes alteradas)
# --incremental  Streaming instal (Android 11+)
```

### Desinstalação
```bash
adb uninstall [-k] <package>           # Remove app
# -k  Manter dados e cache
```

### Transferência de Arquivos
```bash
adb push [--sync] [-z ALG] <local>... <remote>   # Host → Device
adb pull [-a] [-z ALG] <remote>... <local>       # Device → Host
adb sync [-l] [-z ALG] [partição]                # Sync build (system, data, vendor, etc.)

# --sync  Só envia arquivos mais novos (push)
# -a      Preserva timestamp e modo (pull)
```

### Shell Remoto
```bash
adb shell [comando]            # Executa comando único ou shell interativo
adb shell -n                   # Não aloca TTY (para scripts)
adb shell -T                   # Desabilita alocação PTY
adb shell -x                   # Sai se comando falhar
```

### Logs e Depuração
```bash
adb logcat [opções] [filtros]           # Logs do sistema
adb logcat -c                           # Limpa buffers
adb logcat -g                           # Tamanho dos buffers
adb logcat -G <size>                    # Define tamanho buffer (K/M)
adb logcat -f <arquivo>                 # Salva em arquivo
adb logcat *:V                          # Tudo (verbose)
adb logcat -s TAG:V                     # Tag específica

adb bugreport [caminho]                 # Relatório completo (dumpsys+dumpstate+logcat)
adb jdwp                                # PIDs de processos JDWP (debug Java)
adb forward tcp:PORT jdwp:PID           # Port forward para debugger
```

### Gerenciamento de Pacotes (pm)
```bash
adb shell pm list packages              # Todos pacotes
adb shell pm list packages -3           # Só terceiros
adb shell pm list packages -s           # Só sistema
adb shell pm list packages -d           # Desabilitados
adb shell pm list packages -e           # Habilitados
adb shell pm path <package>             # Caminho do APK
adb shell pm dump <package>             # Info completa do pacote
adb shell pm enable <package|component> # Habilita
adb shell pm disable <package|component> # Desabilita
adb shell pm grant <pkg> <perm>         # Concede permissão (API 23+)
adb shell pm revoke <pkg> <perm>        # Revoga permissão
adb shell pm clear <package>            # Limpa dados do app
adb shell pm set-install-location 0|1|2 # Auto/Interno/Externo
```

### Activity Manager (am)
```bash
adb shell am start -n pkg/.Activity     # Inicia Activity
adb shell am start -a ACTION -d URI     # Intenção com ação/dados
adb shell am force-stop <package>       # Para app completamente
adb shell am kill-all                   # Mata todos processos
adb shell am broadcast -a ACTION        # Envia broadcast
adb shell am start-service -n pkg/.Svc  # Inicia Service
```

### Power e Reinicialização
```bash
adb reboot                            # Reinicia normal
adb reboot bootloader                 # Reinicia no fastboot
adb reboot recovery                   # Reinicia no recovery
adb reboot sideload                   # Reinicia no sideload mode
adb sideload <ota.zip>                # Aplica OTA package
adb root                              # Reinicia adbd como root (userdebug/eng)
adb unroot                            # Reinicia adbd sem root
adb remount                           # Remonta partições RW (root)
adb disable-verity                    # Desabilita dm-verity
adb enable-verity                     # Reabilita dm-verity
```

### Screen Capture
```bash
adb shell screencap -p /sdcard/img.png    # Captura tela (PNG)
adb shell screenrecord /sdcard/vid.mp4    # Grava tela (MP4)
# screenrecord opções: --size WxH --bit-rate BPS --time-limit SEC
```

### Informações do Sistema
```bash
adb shell getprop                     # Todas propriedades do sistema
adb shell getprop ro.product.model    # Modelo
adb shell getprop ro.build.version.sdk # API Level
adb shell getprop ro.serialno         # Serial
adb shell wm size                     # Resolução tela
adb shell wm density                  # Densidade
adb shell dumpsys battery             # Status bateria
adb shell dumpsys meminfo <pkg>       # Memória do app
adb shell dumpsys cpuinfo             # CPU info
adb shell dumpsys activity            # Activity stack
adb shell dumpsys window              # Janelas
adb shell dumpsys package <pkg>       # Info completa pacote
```

### Redirecionamento de Portas
```bash
adb forward tcp:HOST_PORT tcp:DEVICE_PORT    # Host → Device
adb forward tcp:HOST_PORT local:SOCKET       # Host → Unix socket device
adb forward --list                           # Lista forwards
adb forward --remove tcp:HOST_PORT           # Remove forward
adb forward --remove-all                     # Remove todos

adb reverse tcp:DEVICE_PORT tcp:HOST_PORT    # Device → Host (reverso)
adb reverse --list
adb reverse --remove tcp:DEVICE_PORT
adb reverse --remove-all
```

### Segurança e Chaves
```bash
adb keygen <arquivo>               # Gera par chaves pública/privada
# Chave pública vai para /data/misc/adb/adb_keys no device
# Permite conexão sem prompt de autorização
```

### mDNS (descoberta local)
```bash
adb mdns check                     # Verifica se mDNS disponível
adb mdns services                  # Lista serviços descobertos
```

## ADB no Ecossistema EcoSystemUmGrau

### Scripts Existentes
- **`scripts/adb-redmi.ps1`** — Gerencia conexão Redmi Note 11 via Tailscale (IP `100.64.71.9`, porta 5555)
- **`scripts/android_diagnostics.py`** — Diagnóstico completo via ADB (bateria, processos, bancos, apps)
- **`scripts/build.ps1`** (em `Android/VoxUmGrau/`) — Usa `adb install` para deploy automático com versionamento

### Padrões de Uso no Ecossistema
```powershell
# Conectar via Tailscale TCP/IP
adb connect 100.64.71.9:5555

# Instalar VoxUmGrau (build.ps1 faz isso)
adb install -r -g app/build/outputs/apk/debug/app-debug.apk

# Diagnóstico bateria
adb shell dumpsys battery

# Logs do app
adb logcat -s VoxUmGrau:* *:E

# Verificar se app instalado
adb shell pm list packages | findstr "voxumgrau"

# Banco de dados da Bíblia
adb shell run-as com.biblia.estudo cat databases/biblia_estudo.db
```

### Integração com Bridge Jarvis
- Bridge monitora `bridge_estado.json` com `ip` do celular (`100.64.71.9`)
- `saude_sistema()` em `jarvis_bridge.py` usa `_cel_bateria()` via ADB
- Android conecta via WebSocket a `100.91.141.101:8765` (PC Tailscale)

## Comandos Avançados e Poderosos

### SQLite Direto no Device
```bash
adb shell sqlite3 /data/data/pkg/databases/db.sqlite "SELECT * FROM table;"
```

### Backup e Restore (sem root)
```bash
adb backup -apk -shared -all -f backup.ab     # Backup completo
adb restore backup.ab                          # Restore
```

### App Ops (permissões granulares)
```bash
adb shell appops get <pkg>                    # Lista ops
adb shell appops set <pkg> <op> allow|ignore|default
```

### Settings (configurações globais)
```bash
adb shell settings list system|secure|global
adb shell settings put secure enabled_accessibility_services <pkg>/<service>
```

### Input Events (automação)
```bash
adb shell input tap x y                       # Toque
adb shell input swipe x1 y1 x2 y2 [duration]  # Deslizar
adb shell input text "texto"                  # Digitar (escapar espaços)
adb shell input keyevent KEYCODE_HOME         # Teclas (KEYCODE_BACK, etc.)
```

### Procstats e Perfilamento
```bash
adb shell procstats --hours 3                 # Stats de processos
adb shell perfetto --help                     # Tracing avançado (Android 10+)
```

### Dex2oat e Compilação
```bash
adb shell cmd package compile -m speed -f <pkg>   # Compila AOT
adb shell cmd package compile -m verify -f <pkg>  # Verifica
```

## Troubleshooting Comum

| Problema | Solução |
|----------|---------|
| `unauthorized` | Aceitar prompt no dispositivo; verificar chave em `~/.android/adbkey` |
| `offline` | `adb kill-server && adb start-server`; reconectar USB/TCP |
| `no devices/emulators found` | Verificar `adb devices`; drivers USB; depuração USB ativada |
| `more than one device` | Usar `-s <serial>` ou `-d`/`-e` |
| `connection refused` (TCP) | `adb tcpip 5555` no device; verificar IP/firewall; mesma rede |
| `adb server version mismatch` | `adb kill-server`; reiniciar; verificar PATH múltiplos ADBs |
| `read-only file system` | `adb root && adb remount` (só userdebug/eng) |
| `INSTALL_FAILED_VERSION_DOWNGRADE` | `adb install -r -d` |

## Boas Práticas para Automação

1. **Sempre use `-s <serial>`** em scripts para evitar ambiguidade
2. **`adb wait-for-device`** antes de comandos críticos
3. **`adb shell -n`** para comandos não-interativos (evita problemas de TTY)
4. **Verifique exit code** — ADB retorna 0 em sucesso, ≠0 em falha
5. **Use `timeout`** em comandos que podem travar
6. **Logcat com filtro** — `adb logcat -s TAG:V *:S` (só TAG, silencia resto)
7. **`--sync` no push** — evita reenviar arquivos inalterados

## Referências Oficiais

- **Documentação Google:** https://developer.android.com/tools/adb
- **Man page oficial:** https://android.googlesource.com/platform/packages/modules/adb/+/refs/heads/master/docs/user/adb.1.md
- **Código fonte ADB:** https://android.googlesource.com/platform/packages/modules/adb/
- **Cheatsheet prático:** https://devhints.io/adb

---

**Status:** Conhecimento ADB consolidado no ecossistema. Jarvis agora é perito operador de ADB — capaz de diagnosticar, instalar, depurar, automatizar e extrair qualquer informação de dispositivos Android via linha de comando.