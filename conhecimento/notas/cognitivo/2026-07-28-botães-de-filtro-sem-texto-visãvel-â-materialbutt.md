---
tags: [cognitivo, dominio, general, nenhum, uniformes, vel]
aliases: [﻿# 2026-07-28: BotÃµes de filtro sem texto visÃ­vel â€” Mate]
date: 2026-08-05
---

# ﻿# 2026-07-28: BotÃµes de filtro sem texto visÃ­vel â€” MaterialButton vs TextView

**Dominio:** general

﻿# 2026-07-28: BotÃµes de filtro sem texto visÃ­vel â€” MaterialButton vs TextView

## Contexto
App Mp3Player Android. 5 botÃµes de filtro no topo da aba "MÃºsicas": Todas, Favoritas, A-Z, Lista, Sel. O texto nÃ£o aparecia â€” os botÃµes ficavam verdes uniformes sem nenhum texto visÃ­vel.

## O que deu errado

### 1. MudanÃ§a de tema AppCompat â†’ MaterialComponents quebrou os botÃµes
- `TagEditorActivity` usava `TextInputLayout` do Material Components, que REQUER tema `MaterialComponents`
- Ao 
## Conexoes

- [[cluster-hub-cognicao]]
- [[cognitivo-hub-cognitivo]]