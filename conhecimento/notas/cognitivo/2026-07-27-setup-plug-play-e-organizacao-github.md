---
tags: [cognitivo, general]
aliases: [﻿# 2026-07-27 - Setup Plug & Play e organizacao GitHub]
date: 2026-07-27
---

# ﻿# 2026-07-27 - Setup Plug & Play e organizacao GitHub

**Dominio:** general

﻿# 2026-07-27 - Setup Plug & Play e organizacao GitHub

## O que foi feito
- Repositorios do GitHub mapeados: 11 existentes, nenhum LER separado
- setup.bat criado: script unico para qualquer PC novo (clona, instala, configura, pede API keys)
- config/opencode.jsonc: template com {{USERPROFILE}} placeholder para geracao dinamica
- config/agents/: fonte unica dos 15 agentes OpenCode (repo eh source of truth)
- config/opencode-model-fallback.jsonc: config do plugin fallback
- Vigilante atualizado:

﻿# 2026-07-27 - Unificacao completa do ecossistema

## Problemas resolvidos
1. **LER fora do repo**: movido ~/.ler/ → ler-runtime/ com junction. Tudo versionado.
2. **Polling ineficiente**: vigilante agora usa FileSystemWatcher + debounce 300ms.
3. **Sync so push**: agora faz pull antes de push (bidirecional).
4. **Sem comando central**: ecosystem.ps1 criado (sync, scan, status).
5. **LER remoto separado**: deletado github.com/idavidjunior/LER, conhecimento unificado.

## Decisoes
- LER runtime 

﻿# 2026-07-27 - Scan proativo: Biblia
## Marcadores encontrados
- parse_apocrypha.py: 1 marcadores
- parse_apocrypha2.py: 1 marcadores
- parse_apocrypha3.py: 1 marcadores
- ResourcesActivity.java: 3 marcadores



﻿# 2026-07-27 - Scan proativo: CellCleaner
## Marcadores encontrados
- MainActivity.java: 1 marcadores



﻿# 2026-07-27 - Scan proativo: Mp3Player
## Marcadores encontrados
- BiquadFilter.kt: 1 marcadores
- EqualizerAudioProcessor.kt: 2 marcadores
- AudioDecoder.kt: 1 marcadores
- EqPresetManager.kt: 2 marcadores
- MainActivity.kt: 2 marcadores
- TagEditorActivity.kt: 1 marcadores



﻿# 2026-07-27 - Scan proativo: SupermarketCalculator
## Marcadores encontrados
- MainActivity.java: 2 marcadores


