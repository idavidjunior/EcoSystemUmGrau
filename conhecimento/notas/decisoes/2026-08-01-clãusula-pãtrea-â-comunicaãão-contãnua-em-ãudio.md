---
tags: [commits, decisao, desrespeitando, fazendo, narrar, opencode]
aliases: [﻿# 2026-08-01: ClÃ¡usula PÃ©trea â€” ComunicaÃ§Ã£o contÃ­nua]
date: 2026-08-05
---

# ﻿# 2026-08-01: ClÃ¡usula PÃ©trea â€” ComunicaÃ§Ã£o contÃ­nua em Ã¡udio

**Fonte:** opencode

﻿# 2026-08-01: ClÃ¡usula PÃ©trea â€” ComunicaÃ§Ã£o contÃ­nua em Ã¡udio

**Categoria:** decisao
**Contexto:** UsuÃ¡rio apontou que o Jarvis executou tarefas (verificaÃ§Ã£o de sync, commits, pronÃºncia) sem narrar em Ã¡udio o que estava fazendo, desrespeitando a regra de comunicaÃ§Ã£o por voz. A regra existia no contexto da sessÃ£o, mas nÃ£o estava registrada em lugar nenhum â€” por isso foi esquecida.

## DecisÃ£o
**Todo passo que o Jarvis executa DEVE ser narrado em Ã¡udio**, sempre, sem exceÃ§Ã£o, em qualquer tarefa.

## Regras permanentes (registradas em scripts/JARVIS_SYSTEM.md)
1. Antes de agir, fale o que vai fazer ("Vou verificar o git...", "Vou commitar...", "Vou testar a pronÃºncia...").
2. Durante a execuÃ§Ã£o, acompanhe em voz ("Encontrei...", "Estou ajustando...", "Agora vou sincronizar...").
3. Ao terminar, resuma em Ã¡udio o que foi feito e o resultado ("Pronto, tudo sincronizado.").
4. Usar o TTS da bridge (`gerar_audio` / `vox_audio.py falar`) para falar.
5. Vale para TODA sessÃ£o e TODA tarefa â€” Ã© clÃ¡usula pÃ©trea, nÃ£o pode ser esquecida.

## ImplementaÃ§Ã£o
- `scripts/JARVIS_SYSTEM.md`: seÃ§Ã£o "ClÃ¡usula PÃ©trea â€” ComunicaÃ§Ã£o em Ãudio" adicionada logo apÃ³s a Identidade.
- O `JARVIS_SYSTEM.md` Ã© injetado pela bridge no prompt de todo agente â€” a regra vale para qualquer sessÃ£o.

## ValidaÃ§Ã£o
- Regra adicionada ao system prompt (lido a cada conexÃ£o) âœ“
- Ãudio de confirmaÃ§Ã£o gerado e tocado âœ“

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]