---
tags: [cognitivo, ecossistema, evoluir, general, precisa, trocar]
aliases: [﻿# Hora na tela vs hora no Ã¡udio (Jarvis)]
date: 2026-08-04
---

# ﻿# Hora na tela vs hora no Ã¡udio (Jarvis)

**Dominio:** general

﻿# Hora na tela vs hora no Ã¡udio (Jarvis)

- **Data:** 31/07/2026
- **SessÃ£o:** ImplementaÃ§Ã£o de `normalizar_hora_display()` na bridge

## Problema
O LLM reescrevia a hora do briefing/saudaÃ§Ã£o em forma falada ("23 horas e 29",
"22 horas em ponto", "meia-noite") no prÃ³prio TEXTO exibido no app. O usuÃ¡rio
deixou claro: **o formato exibido deve continuar `21:44`; sÃ³ a PRONÃšNCIA do
Jarvis precisava ser corrigida.**

## SoluÃ§Ã£o (divisÃ£o de responsabilidades)
- `melhorar_fala(texto)` â†’ 

﻿# Aprendizado â€” 2026-07-31 â€” Horas faladas corretamente no TTS do Jarvis

## Contexto
- O edge-tts lia `21:44` de forma errada (como razÃ£o/hora digital). O usuÃ¡rio trouxe 3 estratÃ©gias e recomendou a **#1: substituiÃ§Ã£o de texto via cÃ³digo antes do TTS**.

## O que foi feito (`scripts/jarvis_bridge.py`)
- Em `melhorar_fala()` (preparaÃ§Ã£o do texto para o Ã¡udio), **antes** da troca de `:` por vÃ­rgula (que comeria o tempo):
  - `(\d{1,2}):00\b` â†’ `\1 horas em ponto` (ex.: "22:00" â†

﻿---
tipo: decisao
tags: [tts, edge-tts, ssml, naturalidade, jarvis, pronuncia, clausula-petrea]
data: 2026-08-02
contexto: ClÃ¡usula pÃ©trea exige comunicaÃ§Ã£o contÃ­nua em Ã¡udio. O edge-tts jÃ¡ suporta SSML completo e o ecossistema precisa evoluir pronÃºncia e naturalidade sem trocar de TTS.
decisao: "Adicionei _ssml_enriquecer() em scripts/jarvis_bridge.py e mudei a ordem em gerar_audio(): phoneme primeiro sobre texto puro, depois SSML enriquece naturalidade."
impacto: "NÃºmeros, percentuai
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]