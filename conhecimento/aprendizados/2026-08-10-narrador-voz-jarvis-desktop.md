---
tipo: padrao
tags: [jarvis, voz, tts, opencode-desktop, sqlite, narrador, audio]
data: 2026-08-10
contexto: "Usuário quer dar voz ao Jarvis no opencode desktop: um processo rodando no computador que reproduza as conversas em áudio em tempo real. O app do celular (VoxUmGrau via jarvis_bridge) não estava dando resultado; rodar no PC deve ser melhor."
decisao: "Criado scripts/narrador_desktop.py: vigia o SQLite do opencode (opencode.db em ~/.local/share/opencode) em modo somente leitura (PRAGMA query_only, uri mode=ro), faz JOIN de part (data JSON type=text) com message (role) e session (título), filtra sessões excluídas (watchdog-health), aplica debounce de 1,5s e fala via vox_audio falar (edge-tts pt-BR-AntonioNeural). Posição salva em runtime/narrador_posicao.json (high-water mark em ms) para continuar de onde parou. Início via narrador_start.bat."
impacto: "Jarvis fala as respostas do assistant em tempo real no PC, sem interferir no desktop (leitura-only, WAL seguro). Validado com o banco real: extração das respostas da sessão ativa e teste de áudio reproduzido. Alternativa ao app do celular."
---

# Aprendizado: Narrador de voz do Jarvis no opencode desktop

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