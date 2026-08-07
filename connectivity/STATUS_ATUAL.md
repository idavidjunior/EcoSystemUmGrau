# Estado Atual das Conexões

**Última verificação:** 2026-08-07 05:40:32

## ADB Status
- Dispositivo conectado: `6d92eed7` (status: device)
- Caminho ADB: `C:\Users\David Jr\AppData\Local\Android\Sdk\platform-tools\adb.exe`
- Estado: ✅ Ativo

## Tailscale Status
- **Conexões ativas:**
  - `100.91.141.101` - desktop-ip8nvql (Windows)
  - `100.120.67.64` - desktop-6i6nsfs (Windows) - offline há 7 dias
  - `100.64.71.9` - redmi-note-11 (Android) - active; direct 192.168.15.4:46689

- Estado: ✅ Online

## Sistemas de Monitoramento
1. **connection_guardian.py** - Daemon de vigilância contínua
2. **watcher.py** - Script para Tarefa Agendada do Windows

## Comandos Úteis
```
adb devices                    # Listar dispositivos
adb connect <ip>              # Conectar dispositivo
tailscale status              # Status da rede
tailscale up                  # Reconectar
python connection_guardian.py --daemon  # Iniciar vigilância
```
