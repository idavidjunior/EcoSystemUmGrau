# Android Diagnostics — Diagnóstico Remoto do VoxUmGrau

## Como usar
Para diagnosticar o aplicativo Android remotamente, use `python EcoSystemUmGrau/scripts/android_diagnostics.py`.

O script conecta via ADB ao dispositivo `100.64.71.9:5555` e coleta:
- Modelo, versão do Android, SDK, fuso horário
- Bateria (nível, temperatura, status de carga)
- Aplicativo (versão, PID, memória, processo ativo ou parado)
- Rede (tipo de conexão, WebSocket na porta 8765)
- Áudio (configurações de áudio, MediaPlayer ativo)
- Últimos logs de erro e aviso do VoxUmGrau

## Exemplo
```bash
python scripts/android_diagnostics.py
# → JSON completo com dispositivo, app, bateria, rede, áudio e logs
```

## Requisitos
- ADB em `C:\Users\Playtec-bancada\AppData\Local\Android\Sdk\platform-tools\adb.exe`
- Dispositivo conectado via Wi-Fi (Tailscale) em `100.64.71.9:5555`
- Pacote do app: `com.voxumgrau.app`
- Python 3.10+ (sem dependências externas)

## Gatilhos
Use esta skill quando o usuário relatar:
- "o app não responde"
- "não está ouvindo"
- "não reproduz áudio"
- "está lento"
- "desconectou"
- qualquer sintoma do aplicativo Android
