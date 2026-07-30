# Android Diagnostics — Diagnóstico Remoto Automático do VoxUmGrau

> **ATUALIZAÇÃO AUTOMÁTICA:** Cada vez que você descobrir um novo bug, padrão, ou conhecimento sobre diagnóstico remoto, ATUALIZE este skill imediatamente. Não peça permissão. Não espere.

## Propósito
Diagnosticar, monitorar e manter o aplicativo Android VoxUmGrau remotamente, sem que o usuário precise fazer nada manualmente. O sistema deve ser proativo: detectar problemas antes do usuário reclamar.

## Arquitetura do Diagnóstico Remoto

```
PC (Jarvis + Bridge + Guardian)              Celular (Android Xiaomi)
┌──────────────────────────────┐             ┌──────────────────────┐
│ system_guardian.py           │             │ VoxUmGrau App        │
│   ↓ monitora RAM/processos  │     ADB     │   WebSocket Client   │
│ android_diagnostics.py      │◄────WiFi───►│   SpeechRecognizer   │
│   ↓ diagnóstico completo    │  Tailscale  │   MediaPlayer        │
│ jarvis_bridge.py             │             └──────────────────────┘
│   ↓ WebSocket server :8765  │
│ watchdog.ps1                 │
│   ↓ reinicia se cair         │
└──────────────────────────────┘
```

## Scripts do Ecossistema

| Script | Caminho | Função |
|--------|---------|--------|
| `android_diagnostics.py` | `scripts/android_diagnostics.py` | Diagnóstico completo do dispositivo Android via ADB |
| `system_guardian.py` | `scripts/system_guardian.py` | Monitor de RAM e processos, mata zumbis automaticamente |
| `guardian_manager.ps1` | `scripts/guardian_manager.ps1` | Gerenciador do guardian: start, stop, restart, status |
| `jarvis_bridge.py` | `scripts/jarvis_bridge.py` | Bridge WebSocket entre Android e OpenCode |
| `watchdog.ps1` | `scripts/watchdog.ps1` | Monitora bridge a cada 20s, reinicia se cair |

## Como Usar

### Diagnóstico completo
```powershell
python scripts/android_diagnostics.py --json
```
Retorna JSON com: dispositivo, app, bateria, rede, áudio, crashes, logs.

### Resumo para TTS (uma linha)
```powershell
python scripts/android_diagnostics.py --resumo
```
Exemplo: "Modelo: 2201117TI | Android: 13 (SDK 33) | Memoria: 142 MB..."

### Auto-teste de conectividade
```powershell
python scripts/android_diagnostics.py --self-test
```
Testa ADB + WebSocket bridge. Retorna "ok" ou a falha específica.

### Guardian - status
```powershell
.\scripts\guardian_manager.ps1 -Action status
```
Mostra se está rodando, RAM livre, disco, últimas ações.

### Guardian - start/stop
```powershell
.\scripts\guardian_manager.ps1 -Action start
.\scripts\guardian_manager.ps1 -Action stop
```

## Diagnóstico Automático (Proativo)

Sempre que o usuário mencionar sintomas abaixo, execute `android_diagnostics.py --json` e analise:

| Sintoma do usuário | O que verificar no diagnóstico |
|--------------------|-------------------------------|
| "o app não responde" | Processo parado, PID ausente, crash no log |
| "não está ouvindo" | WebSocket bridge: status da conexão na porta 8765 |
| "não reproduz áudio" | `audio.player` e `audio.estado` - verificar se é "tocando" |
| "está lento" | Memória do app (>200 MB), bateria em modo economia |
| "desconectou" | Rede: Wi-Fi ou dados móveis, WebSocket status |
| "travou" | `crash_analysis.crashes_detectados` - procurar FATAL EXCEPTION, ANR |
| "a bateria está acabando" | Bateria < 20%, temperatura > 40°C |
| "deu erro" | Logs com NullPointerException, RuntimeException |
| sem sintoma (proativo) | Verificação silenciosa: processo rodando? bridge ok? |

### Gatilhos automáticos (não perguntar, só agir)

1. **Se o guardian matou processo do OpenCode** → informar: "Processo zumbi liberou X MB."
2. **Se ADB perder conexão com o celular** → tentar reconectar: `adb connect 100.64.71.9:5555`
3. **Se a bridge cair** → o watchdog já reinicia, mas avisar: "Bridge reiniciada."
4. **Se o app Android não estiver rodando** → diagnosticar e oferecer: "Quer que eu tente reiniciar o app?"
5. **Se a memória do PC estiver crítica** → guardian já age, só avisar: "RAM crítica, liberei X MB matando processos ociosos."

## Conexão ADB via Tailscale

### Parâmetros fixos
```
Dispositivo: 100.64.71.9:5555
ADB: C:\Users\Playtec-bancada\AppData\Local\Android\Sdk\platform-tools\adb.exe
Pacote: com.voxumgrau.app
Bridge: 100.120.67.64:8765
```

### Reconexão automática (se falhar)
```powershell
adb connect 100.64.71.9:5555
```
Se falhar: primeiro `adb tcpip 5555`, depois `adb connect`.

## Análise de Crashes

O `android_diagnostics.py` detecta automaticamente:

| Padrão | Tipo | Severidade |
|--------|------|------------|
| `FATAL EXCEPTION` | Crash fatal | Crítica |
| `AndroidRuntime` | Exceção não capturada | Crítica |
| `ANR` / `anr_` | App não responde | Alta |
| `NullPointerException` | Null pointer | Alta |
| `RuntimeException` | Erro de runtime | Média |
| `Native crash` / `SIGSEGV` | Crash nativo | Crítica |

## Integração com System Guardian

O `system_guardian.py` roda em loop a cada 20s e:

1. **Protege processos essenciais:** winlogon, explorer, bridge, serve, Tailscale
2. **Mata zumbis:** processos opencode/python parados há horas
3. **Monitora RAM:** crítica <200 MB, alerta <500 MB
4. **Prioridade de eliminação:** opencode/python > powershell > chrome > java
5. **Persiste estado:** em `guardian_state.json` para consulta

## Notificações ao Usuário

Sempre que uma ação automática ocorrer:
- "Atualização: guardian matou PID 1234 (opencode), liberou 475 MB."
- "Atualização: conexão ADB restabelecida com o celular."
- "Atualização: bridge reiniciada pelo watchdog."
- "Atualização: RAM normalizada em 2.3 GB livre."

Nunca agir em silêncio — o usuário explicitamente pediu para ser informado.

## Comandos Rápidos (para respostas TTS curtas)

```powershell
# Diagnóstico + resumo para TTS:
python scripts/android_diagnostics.py --resumo

# Só conectividade:
python scripts/android_diagnostics.py --self-test

# Estado do guardian:
.\scripts\guardian_manager.ps1 -Action status

# Diagnóstico + análise de crashes:
python scripts/android_diagnostics.py --json | python -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d[\"crash_analysis\"][\"crashes_detectados\"])} crashes')"
```

## Known Issues & Fixes

| Issue | Causa | Correção |
|-------|-------|----------|
| ADB perde conexão WiFi | Celular muda de rede ou Tailscale cai | `adb connect 100.64.71.9:5555` automático |
| Bridge cai | OpenCode serve reinicia ou trava | Watchdog reinicia em 20s |
| OpenCode zumbi | `run -c` anterior não finalizou | Guardian mata após RAM < 500 MB |
| Diagnóstico lento | ADB timeout em comandos | Timeout de 15s por comando, fallback silencioso |

## Requisitos
- ADB no PATH ou caminho fixo
- Dispositivo Xiaomi conectado via Tailscale (WiFi)
- Pacote: `com.voxumgrau.app`
- Python 3.10+ com `psutil`, `websockets` (guardian + bridge)
- Bridge rodando na porta 8765
- OpenCode serve na porta 8766
