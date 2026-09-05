---
tags: [cognitivo, deve, dominio, general, pelo, usula]
aliases: [Cláusula Pétrea — Ativação de Voz (Eco System)]
date: 2026-08-20
---

# Cláusula Pétrea — Ativação de Voz (Eco System)

**Dominio:** general

## Pedido do usuário

"Quando eu estiver falando com você pelo PC, você deve ativar o sistema de voz
seguindo as regras do ecossistema. Mesmo que eu abra uma nova sessão. Quando eu
digitar em qualquer sessão: **Ativar Eco**, então você ativa todo o ecossistema e
passa a agir/responder dentro dele. **Desativar Eco** desliga."

## Implementação

Regra adicionada à Constituição em `config/agents/00-system-rules.md`:

- **"Ativar Eco"** â†’ confirmar "Eco ativado. Sistema de voz online." + responder
  com áudio via `jarvis_bridge.py` (porta 8765, TTS `pt-BR-AntonioNeural`,
  base64 MP3) + disparar `python scripts/dialogo.py --modo vad` em background (PC)
- **"Desativar Eco"** â†’ confirmar "Eco desativado. Modo texto restaurado." +
  parar modo voz e finalizar `dialogo.py`
- **Persistência:** vale para QUALQUER sessão nova ou existente.

## Sincronização (3 camadas)

1. `config/agents/00-system-rules.md` (fonte única) — seção adicionada como CLÃUSULA PÉTREA
2. `AGENTS.md` — regenerado via
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]