---
tags: [cerebro vivo opencode, opencode, opencode comando, opencodeopencodeopencodeopencodeopencodeopencodeopencodeopen, padrao, vivo opencode]
aliases: [@ecow e /ecow — abrir/focar o Cerebro Vivo]
date: 2026-08-22
---

# @ecow e /ecow — abrir/focar o Cerebro Vivo

**Fonte:** opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode+opencode

---
tipo: padrao
tags: [widget, cerebro-vivo, opencode, comando, foco-janela, ecow]
data: 2026-08-22
contexto: Usuário pediu comando /ecow e @ecow para abrir o widget Cérebro Vivo; se já aberto, trazer a janela para frente em vez de duplicar.
---

# @ecow e /ecow — abrir/focar o Cerebro Vivo

## Dec; ## Decisão
Três camadas enxutas, sem duplicar lógica de foco fora do widget:

1. **scripts/widget_grafo.py** — quando `instancia_unica()` detecta instância
   já rodando, a nova instância usa ctypes (`FindWindowW(None, "Cerebro Vivo")`
   → `ShowWindow(hwnd, 9)` SW_RESTORE → `SetForegroundWindow(hwn
## Conexoes

- [[2026-08-03-adb-remoto-via-tailscale-script-automatico-de-rot]]
- [[cluster-hub-ecossistema]]
- [[compreensao-de-pedidos-refino-com-a-llm-do-opencode-primaria]]
- [[config-2026-07-28-formato-correto-do-mcp-no-opencode-1187]]
- [[eco-agente-e-comando-global]]
- [[padrao-hub-padroes]]