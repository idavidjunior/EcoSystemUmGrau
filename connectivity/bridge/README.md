# EcoSystemUmGrau - Universal Bridge Resilience

## Visão Geral
Sistema de monitoramento e resiliência multi-protocolo para manter conexões críticas ativas 24/7.

## Protocolos Suportados

| Protocolo | Tipo | Primary | Fallback |
|-----------|------|---------|----------|
| ADB USB | adb_usb | ✅ | adb_tcp, tailscale |
| ADB TCP/IP | adb_tcp | ❌ | adb_usb, tailscale |
| Tailscale Exit | tailscale_exit | ✅ | vpn_alternative |
| HTTP API | http | ✅ | api_remote |
| DNS | dns | ✅ | - |
| MQTT | mqtt | ❌ | mqtt_cloud |
| WebSocket | websocket | ❌ | http_polling |
| SSH | ssh | ❌ | ssh_backup |
| Serial | serial | ❌ | usb_hid |
| VPN | vpn | ❌ | tailscale_exit |

## Comandos de Uso

```bash
# Executar health check manual
python bridge/universal_bridge.py --health

# Iniciar jcomo daemon (vigilância contínua)
python bridge/universal_bridge.py --daemon

# Listar endpoints configurados
python bridge/universal_bridge.py --endpoints

# Ver resumo de uptime
python bridge/universal_bridge.py --summary
```

## Arquitetura de Failover

```
Primary → Fallback Chain
   ↓
adb_usb → adb_tcp → tailscale_forward
   ↓
tailscale_exit → vpn_alternative
   ↓
api_local → api_remote
```

## Auto-Aprendizado
- Falhas registradas em `learning/failures.json`
- Padrões detectados automaticamente
- Ajuste dinâmico de timeouts e intervals
- Histórico de failover preservado

## Status Atual (última verificação)
- Tailscale: ✅ Online (redmi-note-11 ativo)
- DNS: ✅ Resolvendo (8.8.8.8, 1.1.1.1, 192.168.15.1)
- ADB: ⚠️ Dispositivo USB não conectado
- API Local: ⚠️ Porta 8765 retorna 426 (websocket upgrade)
