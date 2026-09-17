---
tags: [google-skills, gemini-live-api-dev, websocket, realtime]
aliases: [Gemini Live API, Live API Dev]
date: 2026-09-15
categoria: google-skills
---

# gemini-live-api-dev — Gemini Live API Development

**Categoria:** google-skills
**Fonte:** mcp/google/habilidades/google-agent-skills/gemini-live-api-dev/

## Papel

Skill oficial para aplicações em tempo real, bidirecionais, com a Gemini Live API via WebSocket: áudio/vídeo/texto contínuos, voz bidirecional, VAD (Voice Activity Detection), raciocínio em background (extended thinking), function calling assíncrono, gerenciamento de sessão, tokens efêmeros, transcrição e tradução ao vivo.

## Pontos chave

- Modelos atuais: `gemini-3.8-live`, `gemini-3.8-live-extended-thinking`, `gemini-3.5-transcribe-live`, `gemini-3.5-live-translate-preview`
- Legados (2.0/2.5/3.1 live) → ver `references/migration.md`
- Áudio de entrada: PCM 16-bit mono 16kHz (`audio/pcm;rate=16000`); saída PCM 24kHz
- Enviar todo input em tempo real via `send_realtime_input` (audio/video/texto); `send_client_content` injeta turnos com roles `user`/`model`
- Eventos podem conter múltiplas partes (áudio + transcrição) — processar todas
- `interaction_status` (`IN_PROGRESS`/`IDLE`) para o modelo extended-thinking; não confiar só em `turn_complete`
- Ferramentas async exigem `behavior="NON_BLOCKING"`
- Limites: ou `TEXT` ou `AUDIO` por sessão (não ambos); sessão audio 15min / audio+video 2min / conexão ~10min; 128k input / 64k output tokens; sem code execution nem URL context
- Tokens efêmeros para client-side (nunca API key no browser)

## Dependências

- `google-genai` >= 2.3.0 (Python) e `@google/genai` >= 2.3.0 (JS/TS)
- Conexão direta via WebSockets; WebRTC via integrações de parceiros (LiveKit, Pipecat, Fishjam, Voximplant, etc.)

## Conexões

- [[cluster-hub-google-skills]] — hub do cluster das skills do Google
- [[google-agent-skills]] — padrão Agent Skills no qual esta skill se baseia
- [[gemini-api-dev]] — skill irmã: SDK, modelos e Interactions API