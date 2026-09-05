---
tags: [fonte, gui, opencode, padrao, part, resolvem]
aliases: [Aprendizado: Narrador de voz do Jarvis no opencode desktop]
date: 2026-08-10
---

# Aprendizado: Narrador de voz do Jarvis no opencode desktop

**Fonte:** opencode

## Resumo

Python + SQLite (somente leitura) resolvem o narrador de voz do desktop.

## Descobertas técnicas

- O desktop grava conversas em `~/.local/share/opencode/opencode.db` (SQLite,
  WAL). Tabelas-chave: `session`, `message` (data JSON com `role`) e `part`
  (data JSON `{"type":"text","text":...}`).
- Leitura segura com `sqlite3.connect('file:...?mode=ro', uri=True)` +
  `PRAGMA query_only` — não conflita com o desktop em WAL.
- Filter no SQL: `p.data LIKE '%"type":"text"%'` + role filtrado em Python.
- `opencode_wrapper.py` (pipe do CLI) NÃO funciona no desktop GUI; vigiar o
  banco é o caminho certo.

## Como usar

- `python scripts/narrador_desktop.py --teste` (testa áudio)
- `python scripts/narrador_desktop.py` (narra em tempo real)
- `scripts\narrador_start.bat` (inicia em background)

## Conexoes

- [[aprendizado-2026-07-31-horas-faladas-corretamente-no-tts-do-]]
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]