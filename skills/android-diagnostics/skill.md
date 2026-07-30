# Android Diagnostics — Diagnóstico Remoto do VoxUmGrau

## Como usar
Para diagnosticar o aplicativo Android remotamente, use `python EcoSystemUmGrau/scripts/android_diagnostics.py`.

## Modos de uso

### Diagnóstico completo (JSON)
```bash
python scripts/android_diagnostics.py
# ou
python scripts/android_diagnostics.py --json
```
Retorna JSON completo com: dispositivo, aplicativo, bateria, rede, áudio, análise de crashes e logs.

### Resumo em linha única (para respostas TTS)
```bash
python scripts/android_diagnostics.py --resumo
# → "Modelo: 2201117TI | Android: 13 (SDK 33) | PID: 10941 | Memoria: 142 MB..."
```

### Auto-teste de conectividade
```bash
python scripts/android_diagnostics.py --self-test
# → "ADB: ok | WebSocket: conectado e respondendo"
```

## O que é diagnosticado
- **Dispositivo**: modelo, versão do Android, SDK, fuso horário
- **Bateria**: nível, temperatura, status de carga
- **Aplicativo**: versão, PID, memória (PSS), processo ativo ou parado
- **Rede**: tipo (Wi-Fi/dados móveis), WebSocket conectado à bridge na porta 8765
- **Áudio**: configurações de áudio, sessão de mídia, estado do MediaPlayer
- **Crashes**: detecção automática de FATAL EXCEPTION, ANR, NullPointerException, RuntimeExcepetion, Native crash, SIGSEGV
- **Logs**: últimas 20 linhas de log do VoxUmGrau com filtro de erros e avisos

## Requisitos
- ADB em `C:\Users\Playtec-bancada\AppData\Local\Android\Sdk\platform-tools\adb.exe`
- Dispositivo conectado via Wi-Fi (Tailscale) em `100.64.71.9:5555`
- Pacote do app: `com.voxumgrau.app`
- Python 3.10+ (sem dependências externas além de `websockets`)
- Bridge Jarvis rodando em `100.120.67.64:8765`

## Gatilhos
Use esta skill quando o usuário relatar:
- "o app não responde"
- "não está ouvindo"
- "não reproduz áudio"
- "está lento"
- "desconectou"
- "o aplicativo travou"
- "deu erro no celular"
- "a bateria está acabando rápido"
- qualquer sintoma do aplicativo Android
