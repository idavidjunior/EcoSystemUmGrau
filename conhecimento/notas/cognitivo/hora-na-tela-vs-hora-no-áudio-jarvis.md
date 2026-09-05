---
tags: [app, cognitivo, corretamente, falada, general, próprio]
aliases: [# Hora na tela vs hora no áudio (Jarvis)]
date: 2026-08-20
---

# # Hora na tela vs hora no áudio (Jarvis)

**Dominio:** general

# Hora na tela vs hora no áudio (Jarvis)

- **Data:** 31/07/2026
- **Sessão:** Implementação de `normalizar_hora_display()` na bridge

## Problema
O LLM reescrevia a hora do briefing/saudação em forma falada ("23 horas e 29",
"22 horas em ponto", "meia-noite") no próprio TEXTO exibido no app. O usuário
deixou claro: **o formato exibido deve continuar `21:44`; só a PRONÚNCIA do
Jarvis precisava ser corrigida.**

## Solução (divisão de responsabilidades)
- `melhorar_fala(texto)` â†’ 

# Aprendizado — 2026-07-31 — Horas faladas corretamente no TTS do Jarvis

## Contexto
- O edge-tts lia `21:44` de forma errada (como razão/hora digital). O usuário trouxe 3 estratégias e recomendou a **#1: substituição de texto via código antes do TTS**.

## O que foi feito (`scripts/jarvis_bridge.py`)
- Em `melhorar_fala()` (preparação do texto para o áudio), **antes** da troca de `:` por vírgula (que comeria o tempo):
  - `(\d{1,2}):00\b` â†’ `\1 horas em ponto` (ex.: "22:00" â†

---
tipo: decisao
tags: [
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]