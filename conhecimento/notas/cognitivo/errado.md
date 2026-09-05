---
tags: [ativo, cognitivo, daemon, general, note, tools]
aliases: [ERRADO]
date: 2026-08-20
---

# ERRADO

**Dominio:** general

## Problema

O scrcpy retornava "Could not find any ADB device" mesmo com Tailscale ativo.

## Causa

O `adb_auto_connect.py` usava um caminho incorreto para o ADB:
```python
# ERRADO
os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk', 'platform-tools', 'adb.exe')
```

O caminho correto no Windows é:
```
%LOCALAPPDATA%\Android\platform-tools\platform-tools\adb.exe
```

## Solução

Corrigido para tentar múltiplos caminhos conhecidos:
1. `%LOCALAPPDATA%\Android\platform-tools\platform-tools\adb.exe` (correto)
2. `%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe` (alternativo)
3. `%PROGRAMFILES%\Android\platform-tools\adb.exe` (fallback)

## Verificação

- `adb_auto_connect.py` agora conecta via Tailscale (100.64.71.9:5555)
- `scrcpy` funciona com o dispositivo Xiaomi Redmi Note 11
- Dispositivo aparece em `adb devices` como "device"

## Fluxo recomendado

1. Rodar `python scripts/adb_auto_connect.py` antes do scrcpy
2. Ou usar `python scripts/scrcpy/scrcpy_daemon.py` que 
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]