---
tags: [anterior, decisao, intacto, opencode, porqu, recurso]
aliases: [@ecow e /ecow — abrir/focar o Cerebro Vivo]
date: 2026-08-22
---

# @ecow e /ecow — abrir/focar o Cerebro Vivo

**Fonte:** opencode

## Decisão
Três camadas enxutas, sem duplicar lógica de foco fora do widget:

1. **scripts/widget_grafo.py** — quando `instancia_unica()` detecta instância
   já rodando, a nova instância usa ctypes (`FindWindowW(None, "Cerebro Vivo")`
   → `ShowWindow(hwnd, 9)` SW_RESTORE → `SetForegroundWindow(hwnd)`) e sai.
   O comportamento "abrir ou focar" vive DENTRO do widget: qualquer launcher se beneficia.
2. **scripts/ecow.bat** — launcher fino no padrão do controle.bat (pythonw, sem console).
3. **Comando `ecow` no config/opencode.jsonc** (repo + deployed, com backup .bak)
   + agente `config/agents/ecow.md` (mode: subagent) para o gatilho @ecow.

## Impacto
- `/ecow` executa via LLM curta (agente ecow); comportamento garantido pelo bat.
- Futuras notas/memórias continuam pulsando em amarelo por 12h (recurso anterior intacto).
- Nenhum processo duplicado nos testes; foco confirmado com hwnd válido.

## Aprendizados
- `Get-Process pythonw` não mostra MainWindowTitle da janela do widget porqu
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]