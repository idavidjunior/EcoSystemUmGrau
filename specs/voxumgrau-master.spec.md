---
id: spec-voxumgrau-master
versao: 1.0.0
status: ativo
componente: Projetos/VoxUmGrau (app Android) + scripts/jarvis_bridge.py (bridge) + EcoSystemUmGrau (runtime)
tags: [voxumgrau, voz, eco, websocket, bridge, stt, tts, historico-compartilhado, autonomia]
data: 2026-09-07
---

# Spec Mestre — VoxUmGrau: A Voz do EcoSystemUmGrau

## Visão Geral

O **VoxUmGrau** é a **interface de voz** do EcoSystemUmGrau. Ele **não é um app separado** — é a **voz** do ecossistema, compartilhando:
- **Histórico** (conversa_unica.json)
- **Memória** (memory_engine, conhecimento/aprendizados)
- **Análise** (runtime_context, context-engine, auditoria)
- **Execução** (bridge -> opencode serve -> LER -> agentes)
- **Estado** (runtime/state.json, runtime/autonomia)

> **Regra de Ouro**: O app Android **não mantém estado próprio**. Ele apenas **renderiza** e **captura voz**. Todo poder reside no EcoSystemUmGrau (PC).

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        USUÁRIO (Voz)                            │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VoxUmGrau (Android App)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  VoxStt     │  │ VoxWebSocket│  │  VoxAudioPlayer         │ │
│  │ (SpeechRec) │◄─┤ (WS + HB)   │  │ (edge-tts MP3)          │ │
│  └──────┬──────┘  └──────┬──────┘  └────────────┬────────────┘ │
└─────────┼────────────────┼───────────────────────┼──────────────┘
          │                │                       │
          ▼                ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    JARVIS_BRIDGE (Python)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  opencode   │  │   TTS/STT   │  │  EcoSystemUmGrau APIs   │ │
│  │   serve     │  │ (edge-tts)  │  │  (memory, context, LER) │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ECO SYSTEM UM GRAU                           │
│  • runtime/state.json        • conhecimento/memoria/           │
│  • runtime/autonomia/        • scripts/ (agentes, LER, skills) │
│  • conversa_unica.json       • config/opencode.jsonc           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Protocolo WebSocket (v2)

### Mensagens App → Bridge
```json
{"tipo": "mensagem", "id": 1, "texto": "fala do usuário"}
{"tipo": "editar", "id": 2, "texto_antigo": "...", "texto_novo": "..."}
{"tipo": "ping"}
```

### Mensagens Bridge → App
```json
{"tipo": "historico", "mensagens": [{"texto": "...", "de_usuario": true}, ...]}
{"tipo": "mensagem", "id": 1, "texto": "resposta", "progresso": "etapa"}
{"tipo": "editar", "corrigido": "novo texto"}
{"tipo": "imagem", "base64_png": "...", "legenda": "..."}
{"tipo": "pong"}
{"tipo": "ack", "ack": 1}
{"tipo": "audio_streaming", "text": "..."}
{"tipo": "audio_chunk", "audio_chunk": "base64"}
{"tipo": "audio_done"}
{"tipo": "audio", "audio": "base64", "text": "..."}
```

---

## Funcionalidades Obrigatórias

### 1. Conexão Resiliente (✅ Implementado)
- **Backoff exponencial + jitter** (1s → 2s → 4s → 5s teto)
- **Heartbeat app-level** 15s (ping/pong) + ping nativo OkHttp 180s
- **Grace period 90s** no setup (bridge saudação LLM+TTS)
- **Fila ACK-based** — reenvio automático ao reconectar
- **Sonda TCP** (1.5s/host) para troca de rota Wi-Fi↔dados/VPN
- **Vigia de rota** — detecta roteamento quebrado por VPN

### 2. Histórico Compartilhado (✅ Implementado)
- **Fonte única**: `conversa_unica.json` no EcoSystemUmGrau
- App **não mantém histórico** — recebe `tipo="historico"` na conexão
- **Edit-and-resubmit**: edita mensagem → bridge trunca histórico → regenera resposta

### 3. Voz Contínua / Modo Eco (✅ Implementado)
- **VAD hands-free** (SpeechRecognizer) — `tentarOuvir()` auto-retrigger
- **Eco toggle** persistido (`SharedPreferences: eco_ativo`)
- **Audio streaming** chunked (baixa latência) + fallback MP3 completo

### 4. TTS Português Natural (✅ Implementado)
- **edge-tts** (pt-BR-AntonioNeural) — **sem SSML** (edge-tts ≥7.x escapa tags)
- **Pronúncias custom** via `pronuncias.json` (campo `fala`: grafia falada)
- **Normalização**: horas, vírgulas de respiração, numerais por extenso
- **SpeechPipeline** (quando disponível) — fallback legado robusto

### 5. Detecção de Intenção Visual (🔄 Parcial - Spec existe, falta implementar)
- **Gatilhos**: "mostre um mapa mental", "faça um diagrama", "desenhe um gráfico", "gere uma figura"
- **Bridge detecta** → gera PNG local (Graphviz) → Base64 → `tipo="imagem"`
- **App renderiza** no `MessageBubble` com legenda

### 6. Tarefas Assíncronas com Aviso Periódico (✅ Implementado)
- **Fila persistente** (`runtime/tarefas_async.json`)
- **Executor** em subprocesso (auditoria, integridade, preflight)
- **Aviso periódico** configurável ("me avise a cada 5 min")
- **Notificação proativa** via WS para app Android

### 7. Saúde do Sistema & Briefing (✅ Implementado)
- **PC**: CPU, RAM, bateria, disco (PowerShell WMI)
- **Celular**: bateria via ADB (`dumpsys battery`)
- **Briefing espontâneo** na conexão: data/hora, clima (Open-Meteo), previsão, feriados, pico trânsito, saúde

### 8. Auto-healing & Monitoramento (✅ Implementado)
- **system_guardian.py**: limpa CLI órfãos, detecta duplicatas singleton
- **runtime_maestro.py**: livro único de processos, cooldown global
- **opencode_desktop_guardian.ps1**: monitora renderer crash/stall, RAM
- **VoxWebSocket**: grace period, heartbeat, vigia de rota

---

## O Que Precisa Ser Implementado (Gaps)

| Funcionalidade | Status | Arquivos |
|---|---|---|
| **Detecção intenção visual** | ❌ Falta | `jarvis_bridge.py` |
| **DiagramGenerator/GraphvizGenerator** | ❌ Falta | `jarvis_bridge.py` (novo módulo) |
| **Tipo `imagem` no VoxWebSocket** | ❌ Falta | `VoxWebSocket.kt` |
| **ImageMessage no VoxViewModel** | ❌ Falta | `VoxViewModel.kt` |
| **Renderização imagem no MessageBubble** | 🟡 Parcial (campo existe) | `MessageBubble.kt` |
| **Limite payload 5MB / fallback** | ❌ Falta | bridge + app |
| **Teste heartbeat com imagem** | ❌ Falta | teste automatizado |

---

## Plano de Implementação (Ordem)

1. **Bridge: Detecção + Geração**
   - Adicionar `DiagramGenerator` protocol em `jarvis_bridge.py`
   - Implementar `GraphvizGenerator` (DOT → PNG)
   - Detectar gatilhos no `caminho_rapido` / processamento normal
   - Converter PNG → Base64, validar ≤ 5MB, enviar `tipo="imagem"`

2. **App: Recepção + Modelo**
   - `VoxWebSocket.kt`: processar `tipo="imagem"` em `processarMensagem()`
   - `VoxViewModel.kt`: adicionar `Mensagem` com `imagem: ByteArray?`, `legenda: String?`
   - `MessageBubble.kt`: variant visual já suporta `imagem`/`legenda` — garantir uso correto

3. **Validação**
   - Build `./gradlew assembleDebug`
   - `adb install -r app/build/outputs/apk/debug/app-debug.apk`
   - Teste manual: "mostre um mapa mental sobre X"
   - Verificar heartbeat/grace period durante geração

---

## Critérios de Aceitação (Definition of Done)

- [ ] Bridge detecta "mostre um mapa mental sobre X" e gera PNG
- [ ] Bridge envia `{"tipo":"imagem","base64_png":"...","legenda":"..."}`
- [ ] App decodifica Base64, cria `ByteArray`, adiciona ao histórico
- [ ] `MessageBubble` renderiza imagem com legenda, respeita largura tela
- [ ] Duas imagens consecutivas coexistem no histórico
- [ ] Payload > 5MB → fallback textual automático
- [ ] Graphviz ausente → fallback textual
- [ ] Heartbeat (15s) e grace period (90s) **não quebram** durante geração
- [ ] `installDebug` SUCCESS, APK instalado no dispositivo via ADB/Tailscale
- [ ] Screenshot/evidência obtida
- [ ] Código versionado via `persistencia.ps1`

---

## Referências

- Spec imagem: `specs/voxumgrau-exibir-imagem.spec.md`
- Bridge: `scripts/jarvis_bridge.py`
- App: `Projetos/VoxUmGrau/app/src/main/java/com/voxumgrau/app/`
- WebSocket: `VoxWebSocket.kt`, `VoxViewModel.kt`, `MessageBubble.kt`
- TTS: `scripts/tts/` (SpeechPipeline, text_normalizer)
- Memória: `scripts/memory_engine.py`, `conhecimento/aprendizados/`