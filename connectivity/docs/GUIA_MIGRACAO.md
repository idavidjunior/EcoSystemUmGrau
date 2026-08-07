# 🚀 Guia de Migração - Bridge Resilience v2.0

## ✅ Pré-requisitos

### 1. Python 3.12+
- Baixar: https://python.org
- **Instalar com PATH no ambiente** (marcar durante instalação)

### 2. ADB (Android Debug Bridge)
```
# Windows: Instalar via Android SDK
choco install adb
# ou baixar platform-tools directamente
# https://developer.android.com/studio/releases/platform-tools
```

### 3. Tailscale
```
# Windows
winget install Tailscale.tailscale
# ou baixar de https://tailscale.com/download
```

## 📋 Passo a Passo de Instalação

### Passo 1: Clonar Repositório
```
git clone https://github.com/seu-usuario/EcoSystemUmGrau.git
cd EcoSystemUmGrau
```

### Passo 2: Instalar Dependências
```
pip install -r connectivity/bridge/requirements.txt
```

### Passo 3: Copiar Auto-Start
```
# Windows: Copiar para Startup
copy connectivity\bridge\auto_start.bat "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\"
```

### Passo 4: Configurar Endpoints
Editar: connectivity/bridge/configs/bridge_config.json
- Atualizar IPs dos dispositivos
- Configurar caminhos de ADB
- Ajustar endpoints SSH/HTTP conforme ambiente

### Passo 5: Testar Manualmente
```
python connectivity/bridge/universal_bridge.py --health
python connectivity/bridge/universal_bridge.py --endpoints
```

### Passo 6: Iniciar Daemon
```
python connectivity/bridge/universal_bridge.py --daemon
```

## 🔧 Configurações Específicas por Sistema

### Windows
- Auto-start via Startup Folder
- ExecutionPolicy: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Tailscale como serviço Windows

### Linux
- Systemd service: `/etc/systemd/system/bridge-resilience.service`
- Auto-start via systemctl
- ADB path: `/usr/bin/adb`

### macOS
- LaunchAgent plist para auto-start
- ADB via Homebrew: `brew install android-platform-tools`

## 📦 Conteúdo da Pasta
```
connectivity/
├── bridge/
│   ├── universal_bridge.py       # Main daemon
│   ├── core.py                   # Health checkers
│   ├── auto_start.bat            # Auto-start Windows
│   ├── start_daemon.bat          # Script de inicialização
│   ├── configs/
│   │   └── bridge_config.json    # Endpoints configuráveis
│   ├── health/                  # Relatórios de saúde
│   ├── learning/               # Patrones de falha aprendidos
│   ├── docs/                   # Esta documentação
│   └── events.jsonl            # Log de eventos
└── bridge_resiliencia.py       # Sistema legacy (compatibilidade)
```

## 🎯 Verificação de Instalação
```
# 1. Daemon rodando?
tasklist | findstr universal_bridge

# 2. Endpoints configurados?
python connectivity/bridge/universal_bridge.py --endpoints

# 3. Conexões ativas?
python connectivity/bridge/universal_bridge.py --health

# 4. Logs gerando?
Get-Content connectivity/bridge/events.jsonl -Tail 5
```

## 🆘 Solução de Problemas Comuns

| Problema | Causa | Solução |
|----------|-------|---------|
| ADB não encontrado | ADB não no PATH | Instalar Android SDK platform-tools |
| Tailscale offline | Serviço parado | `tailscale up` como administrador |
| Daemon não inicia | ExecutionPolicy | `Set-ExecutionPolicy RemoteSigned` |
| Health reports vazios | Endpoints mal configurados | Verificar bridge_config.json |
| Auto-start não funciona | Windows Startup bloqueado | Verificar antivírus/permissionamento |
