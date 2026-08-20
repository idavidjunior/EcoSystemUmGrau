---
tipo: erro
tags: [adb, tailscale, scrcpy, android, conexao]
data: 2026-08-18
contexto: scrcpy nao encontrava dispositivo ADB via Tailscale
decisao: Corrigir caminho do ADB em adb_auto_connect.py para tentar multiplos caminhos
impacto: Tailscale agora funciona como alternativa viavel para conexao ADB
---

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
2. Ou usar `python scripts/scrcpy/scrcpy_daemon.py` que chama auto_connect automaticamente
3. Tailscale IP: 100.64.71.9 (Redmi Note 11)

## Atualização 2026-08-18 - Resiliência ADB

### Problema novo: ADB trava comandos longos

Durante desenvolvimento do app Bíblia, o ADB trava comandos como `logcat` e `uiautomator dump` por tempo indeterminado. Causas identificadas:

1. **ADB server sobrecarregado**: Múltiplos comandos concorrentes causam lock
2. **Timeout insuficiente**: Comandos como `adb shell logcat` precisam de timeout maior
3. **USB instável**: Conexão USB pode cair durante operações longas
4. **Tailscale interfere**: VPN pode causar latência adicional em comandos wireless

### Solução implementada

Criado `scripts/adb_resilient.py` com:
- **Retry automático**: 3 tentativas com restart do ADB server entre elas
- **Timeout configurável**: Default 15s, instalacao 60s
- **Reconexao automatica**: Kill + start server quando timeout ocorre
- **Verificacao pos-instalacao**: Checa PID do app apos instalar

### Padrão para futuros projetos Android

Sempre usar o script resiliente para:
- Instalar APK: `python scripts/adb_resilient.py install`
- Verificar status: `python scripts/adb_resilient.py status`
- Ler erros: `python scripts/adb_resilient.py logcat`
- Reiniciar ADB: `python scripts/adb_resilient.py restart`

### Lição aprendida

Nunca confiar que ADB vai funcionar sempre. Sempre:
1. Verificar conexao antes de comandos criticos
2. Usar retry com backoff
3. Ter script de fallback para restart
4. Nao usar `adb shell logcat` sem timeout - pode travar para sempre
