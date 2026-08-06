---
tags: [chega, cognitivo, fala, general, melodia, vivo]
aliases: [﻿# Aprendizado â€” 2026-07-31 â€” PontuaÃ§Ã£o automÃ¡tica de]
date: 2026-08-06
---

# ﻿# Aprendizado â€” 2026-07-31 â€” PontuaÃ§Ã£o automÃ¡tica de transcriÃ§Ãµes de voz (Jarvis)

**Dominio:** general

﻿# Aprendizado â€” 2026-07-31 â€” PontuaÃ§Ã£o automÃ¡tica de transcriÃ§Ãµes de voz (Jarvis)

## Contexto
- O Android STT (SpeechRecognizer) devolve texto corrido, sem pontuaÃ§Ã£o e **sem prosÃ³dia** (a melodia da fala nÃ£o chega Ã  bridge). O usuÃ¡rio pediu: `?` em perguntas, pontuaÃ§Ã£o correta e **primeira letra maiÃºscula** sempre.
- JÃ¡ existia `fix_punctuation()` bÃ¡sico; a reivisÃ£o ampliou regras e corrigiu um bug de acentuaÃ§Ã£o.

## O que foi feito (`scripts/jarvis_bridge.py`)
1. **Clas

﻿# Aprendizado â€” 2026-07-31 â€” Reorg: catÃ¡logo Ãºnico Habilidades/ + caminhos novos

## Contexto
- Skills estavam espalhadas em `skills/` e `scripts/` (clima, busca), e o array `plugin` do opencode.jsonc apontava para `plugins/ponytail` (inexistente â€” ClÃ¡usula PÃ©trea). DecisÃ£o `2026-07-31-habilidades-catalogo-unico-jarvis.md`: Habilidades = aÃ§Ãµes executÃ¡veis; Agentes = tomadores de decisÃ£o (nÃ£o mexer).

## O que foi feito
1. **`Habilidades/`** â€” catÃ¡logo Ãºnico, 38 habilidades:


﻿# PolÃ­tica de Resposta RÃ¡pida â€” caminhos rÃ¡pidos constantes no Jarvis

- **Data:** 01/08/2026
- **SessÃ£o:** Ensino permanente de caminhos de resposta rÃ¡pida + otimizaÃ§Ã£o de latÃªncia

## Pedido do usuÃ¡rio
"Ensine o Jarvis a SEMPRE procurar caminhos de rÃ¡pida resposta nas conexÃµes e
caminhos de conexÃ£o mais rÃ¡pidas para respostas mais rÃ¡pidas. Isso deve ser
constante."

## O que foi feito

### 1. PolÃ­tica permanente no prompt (JARVIS_SYSTEM.md)
Nova seÃ§Ã£o logo apÃ³s "Identidade

﻿# PontuaÃ§Ã£o da transcriÃ§Ã£o voltando ao balÃ£o do app (corrigido)

- **Data:** 01/08/2026
- **SessÃ£o:** Bug â€” "Que horas sÃ£o" transcrito sem o sinal "?"

## Problema
O usuÃ¡rio perguntou "Que horas sÃ£o" e o balÃ£o da transcriÃ§Ã£o no app nÃ£o mostrava
o "?". A pontuaÃ§Ã£o JÃ era aplicada pela bridge (`fix_punctuation`), mas o app
exibia a transcriÃ§Ã£o crua do STT â€” a correÃ§Ã£o nunca voltava para a tela.

## Causa raiz
- App (`VoxViewModel.onSttResult`): `mensagens + Mensagem(texto,

---
tipo: aprendizado
tags: [jarvis-bridge, voz, widget, grafo, pywebview, comando-voz, cerebro-vivo]
data: 2026-08-04
contexto: Usuario pediu o 'foco vocal via Jarvis' — comando de voz orienta o grafo do conhecimento (cerebro vivo). Bridge Jarvis roda na porta 8765 (processo separado) e o widget do grafo (pywebview) e outro processo; sem API entre eles.
decisao: Usar o filesystem como canal entre processos (o widget ja vigia arquivos do vault). (1) jarvis_bridge._comando_grafo(t) em caminho_rap
## Conexoes

- [[cluster-hub-cognicao]]
- [[cognitivo-hub-cognitivo]]