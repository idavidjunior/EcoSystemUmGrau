---
tags: [blocante, mouse, opencodeopencode, padrao, server, signal]
aliases: [Pesquisa — Interfaces de Conversa (Hermes e outros)]
date: 2026-09-03
---

# Pesquisa — Interfaces de Conversa (Hermes e outros)

**Fonte:** opencode+opencode

## Hermes Agent (Nous Research)

Hermes é um agente com loop de aprendizado embutido; interface primária é TUI
(terminal), com gateway para Telegram/Discord/Slack/WhatsApp/Signal e API server
OpenAI-compatível. Licença MIT.

### Filosofia de interface
- CLI é um TUI completo (não web UI): edição multilinha, autocomplete de
  slash-command, histórico de conversa, interromper-e-direcionar, streaming.
- TUI moderno com modais, seleção por mouse e input não-blocante (`hermes --tui`).
- "Vive onde você está": um único processo gateway atende várias plataformas.
- Continuidade cross-platform de conversa.

### Comandos/sessão (padrões)
- `hermes` (interativo), `hermes chat -q "..."` (query única), `--query-file` (input verbatim).
- `-c`/`--continue` retoma sessão; `-c` é terminal-aware (breadcrumb por terminal:
  tmux pane, wezterm pane, etc.) — cada terminal continua sua própria conversa.
- `--resume <session_id>` / `latest`; `--model`, `--provider`, `--toolsets`, `-s` (skills).
- `-w` isola
## Conexoes

- [[aegis-barra-progresso-tempo-real]]
- [[certificacao-forense-de-processos-boot-do-watchdog]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-4-teste-do-ciclo-de-polling]]
- [[padrao-hub-padroes]]
- [[saudacoes-inteligentes-reconexao-vs-primeira-vez]]