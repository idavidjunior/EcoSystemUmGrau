# Arquitetura Jarvis — Assistente de Voz do Ecossistema

## Visão Geral

```
┌─────────────────────────────────────────────────────┐
│                    PC (Windows)                      │
│                                                     │
│  ┌──────────┐   WebSocket   ┌────────────────────┐  │
│  │ Vigilante ├──────────────► Notifier Bridge      │  │
│  │ (eventos) │              │ (notifier_bridge.py) │  │
│  └──────────┘              └──────────┬────────────┘  │
│                                       │               │
│  ┌──────────────────┐                │               │
│  │ MCP Knowledge     │◄───────────────┘               │
│  │ Server (port????) │                                │
│  └──────────────────┘                                │
└──────────────────────────────────┬───────────────────┘
                                   │ Wi-Fi / LAN
                                   ▼
┌─────────────────────────────────────────────────────┐
│                 Smartphone Android                    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │          Jarvis App (Kotlin)                │    │
│  │                                             │    │
│  │  ┌─────────────┐   ┌──────────────────┐    │    │
│  │  │ MCP Client   │   │ TTS Engine       │    │    │
│  │  │ (consulta    │   │ (voz Jarvis)     │    │    │
│  │  │  ecossistema)│   └──────────────────┘    │    │
│  │  └──────┬──────┘                           │    │
│  │         │                                   │    │
│  │  ┌──────▼──────────────────────────────┐   │    │
│  │  │  Foreground Service                 │   │    │
│  │  │  ● Notifica tarefa concluída        │   │    │
│  │  │  ● Resume resultado em voz          │   │    │
│  │  │  ● Funciona com tela desligada      │   │    │
│  │  └─────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

## Componentes

### PC (EcoSystemUmGrau)

| Componente | Descrição |
|---|---|
| `scripts/notifier_bridge.py` | Novo módulo. Escuta eventos do vigilante via pipe, conecta WebSocket com app Android |
| `scripts/mcp-knowledge-server.py` | Já existe. App consulta para obter status, últimas tasks, health check |
| `scripts/vigilante.ps1` | Já existe. Dispara sinal para notifier_bridge quando learn/sync conclui |

### Smartphone (App Android)

| Componente | Descrição |
|---|---|
| **Foreground Service** | Serviço persistente (notificação "Jarvis ativo"), reconecta WebSocket automaticamente |
| **MCP Client** | HTTP/WebSocket client que chama o MCP Server no PC via LAN |
| **TTS Engine** | Android `TextToSpeech` API. Voz: baixar voice data do Jarvis (Marvel) ou treinar com ElevenLabs |
| **Event Bus** | Processa eventos: `task_complete`, `error`, `sync_done`, `daily_summary` |
| **Voice Scheduler** | Fala apenas em momentos apropriados (ex: não fala se estiver em chamada) |

## Fluxo de uma Tarefa

```
1. Vigilante detecta mudança / learn concluído
2. Vigilante → Notifier Bridge: "task_complete: learn executado, 3 aprendizados novos"
3. Notifier Bridge → WebSocket → App Android
4. App recebe evento, acorda (se dormindo)
5. App consulta MCP Server para detalhes:
   - search-knowledge("ultimas tarefas")
   - get-memory-context()
6. App gera resumo e fala com voz Jarvis:
   "Comandante, o learn foi concluído. Três novos aprendizados foram registrados:
    correção do Equalizer, padrão de busca Android e melhoria no cache."
```

## Tecnologias

| Lado | Tecnologia |
|---|---|
| PC (bridge) | Python + `websockets` (biblioteca padrão) |
| PC (MCP) | Já existe, JSON-RPC stdin/stdout |
| Android (app) | Kotlin + Jetpack Compose + ViewModel |
| Android (service) | `ForegroundService` + `NotificationChannel` |
| Android (rede) | OkHttp WebSocket client |
| Android (voz) | `android.speech.tts.TextToSpeech` |
| Comunicação | WebSocket (eventos push) + HTTP (consultas MCP) |

## Próximos Passos (se quiser implementar)

1. Criar `scripts/notifier_bridge.py` (event loop WebSocket)
2. Adaptar vigilante para notificar bridge
3. Criar app Android (Kotlin) com foreground service
4. Configurar voice data Jarvis
5. Testar em rede local
