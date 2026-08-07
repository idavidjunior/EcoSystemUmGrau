# Deployment Package - Bridge Resilience

Este pacote permite restaurar todo o sistema de conectividade em uma nova máquina.

## Conteúdo

| Arquivo | Descrição |
|---------|-----------|
| `bridge_config.example.json` | Template de configuração de endpoints (versionável - COPIE para `../bridge/configs/bridge_config.json` e personalize) |
| `bridge_export.json` | Export completo do estado atual (endpoints + learning + status) - gerado pelo `bridge_exporter.py` |
| `deploy_bridge.sh` | Script de deploy automático para Linux/macOS |
| `bridge-resilience.service` | Service systemd para Linux |
| `windows_startup.bat` | Auto-start para Windows (copiar para pasta Startup) |

## Como migrar para nova máquina

### Windows
1. Clonar o repositório EcoSystemUmGrau
2. Instalar Python 3.12+ (com PATH), ADB, Tailscale
3. `pip install -r connectivity/bridge/requirements.txt`
4. Copiar `windows_startup.bat` para `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`
5. Copiar `bridge_config.example.json` → `connectivity/bridge/configs/bridge_config.json`
6. Personalizar IPs/caminhos
7. Testar: `python connectivity/bridge/universal_bridge.py --health`
8. Iniciar daemon: `python connectivity/bridge/universal_bridge.py --daemon`

### Linux (systemd)
1. Clonar repositório em `/opt/EcoSystemUmGrau`
2. Rodar: `bash connectivity/deployment/deploy_bridge.sh`
3. Personalizar `connectivity/bridge/configs/bridge_config.json`

## Comandos de export/import

```bash
# Exportar estado atual (endpoints + aprendizado)
python connectivity/bridge/bridge_exporter.py export

# Importar estado em nova máquina
python connectivity/bridge/bridge_exporter.py import

# Gerar pacote de deploy
python connectivity/bridge/bridge_exporter.py deploy
```

## Nota sobre configurações
- `bridge_config.json` contém IPs/caminhos específicos da máquina (NÃO versionado)
- `bridge_config.example.json` é o template versionável (placeholders `SEU_USUARIO`, `IP_...`)
- `bridge_export.json` é um snapshot do estado - regerar antes de migrar
