# EcoSystemUmGrau - Bridge Resilience v2.0

## 🌐 Protocolos Monitorados (12)
| Protocolo | Tipo | Primary | Fallback Chain | Intervalo |
|-----------|------|---------|----------------|-----------|
| ADB USB | adb_usb | ✅ | adb_tcp → tailscale | 15s |
| ADB TCP/IP | adb_tcp | ❌ | adb_usb → tailscale | 15s |
| Tailscale Exit | tailscale | ✅ | vpn_alternative | 15s |
| API Local | http | ✅ | api_remote | 20s |
| DNS | dns | ✅ | - | 30s |
| SSH Primary | ssh | ❌ | ssh_backup → tailscale | 30s |
| SSH Backup | ssh | ❌ | ssh_primary | 30s |
| MQTT Broker | mqtt | ❌ | mqtt_cloud | 30s |
| WebSocket | websocket | ❌ | http_polling | 30s |
| VPN | vpn | ❌ | tailscale | 30s |
| Serial | serial | ❌ | usb_hid | 30s |
| USB HID | usb_hid | ❌ | serial | 30s |

## 🔄 Estratégias de Resiliência

### 1. Failover em Cascata
```
Primary falha → 1° fallback → 2° fallback → 3° fallback → alerta crítico
```

### 2. Auto-Recuperação
- **ADB TCP/IP**: Reconexão automática ao dispositivo Android via WiFi
- **Tailscale**: Reinício automático do serviço (`tailscale up`)
- **SSH**: Reconexão com tentativa de porta alternativa (2222)
- **HTTP**: Retry com backoff exponencial
- **DNS**: Alternância entre resolvedores (8.8.8.8, 1.1.1.1, local)

### 3. Prevenção Preditiva
- Análise de padrões de falha (hourly_failure_analysis)
- Ajuste dinâmico de intervalos baseado em estabilidade
- Aprendizado contínuo de endpoints mais problemáticos

### 4. Auto-Start Configuration
- **Windows Startup Folder**: `EcoSystemUmGrau_Bridge.bat`
- **Daemon oculto**: `python universal_bridge.py --daemon`

## 📁 Estrutura de Arquivos
```
connectivity/
├── bridge/
│   ├── core.py                    # Health check methods
│   ├── universal_bridge.py        # Main daemon + failover
│   ├── start_daemon.bat           # Script de inicialização
│   ├── auto_start.bat             # Auto-start Windows
│   ├── configs/
│   │   └── bridge_config.json     # Configuração de endpoints
│   ├── health/                    # Relatórios de saúde
│   ├── learning/                  # Histórico de falhas
│   └── events.jsonl               # Log de eventos em tempo real
└── bridge_resiliencia.py         # Sistema herdado (legacy)
```

## 🚀 Comandos Úteis
```bash
# Verificar status atual
python EcoSystemUmGrau/connectivity/bridge/universal_bridge.py --health

# Iniciar daemon
python EcoSystemUmGrau/connectivity/bridge/universal_bridge.py --daemon

# Listar endpoints
python EcoSystemUmGrau/connectivity/bridge/universal_bridge.py --endpoints

# Ver resumo de uptime
python EcoSystemUmGrau/connectivity/bridge/universal_bridge.py --summary

# Ver logs em tempo real
Get-Content EcoSystemUmGrau/connectivity/bridge/events.jsonl -Wait
```

## 📊 Status Atual
- **Daemon**: ✅ Executando (auto-start configurado)
- **Tailscale**: ✅ Online (3 nós ativos)
- **DNS**: ✅ Funcional (3 resolvedores)
- **ADB**: ⚠️ USB desconectado (device não conectado)
- **API Local**: ⚠️ Porta 8765 (Upgrade Required - websocket)
- **SSH/MQTT/WebSocket**: ❌ Endpoints não disponíveis (backup ativo via Tailscale)

## 📈 Métricas de Uptime (24h)
- Tailscale: 99.9%
- DNS: 100%
- ADB USB: 0% (sem dispositivo)
- API Local: 95% (intermitente 426)
