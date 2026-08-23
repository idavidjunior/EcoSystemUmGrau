---
tags: [adb, cognitivo, general, independente, trocar, usb]
aliases: [# Hora na tela vs hora no áudio (Jarvis)]
date: 2026-08-23
---

# # Hora na tela vs hora no áudio (Jarvis)

**Dominio:** general

# Hora na tela vs hora no áudio (Jarvis)

- **Data:** 31/07/2026
- **Sessão:** Implementação de `normalizar_hora_display()` na bridge

## Problema
O LLM reescrevia a hora do briefing/saudação em forma falada ("23 horas e 29",
"22 horas em ponto", "meia-noite") no próprio TEXTO exibido no app. O usuário
deixou claro: **o formato exibido deve continuar `21:44`; só a PRONÚNCIA do
Jarvis precisava ser corrigida.**

## Solução (divisão de responsabilidades)
- `melhorar_fala(texto)` â†’ 

# Aprendizado — 2026-07-31 — Horas faladas corretamente no TTS do Jarvis

## Contexto
- O edge-tts lia `21:44` de forma errada (como razão/hora digital). O usuário trouxe 3 estratégias e recomendou a **#1: substituição de texto via código antes do TTS**.

## O que foi feito (`scripts/jarvis_bridge.py`)
- Em `melhorar_fala()` (preparação do texto para o áudio), **antes** da troca de `:` por vírgula (que comeria o tempo):
  - `(\d{1,2}):00\b` â†’ `\1 horas em ponto` (ex.: "22:00" â†

---
tipo: decisao
tags: [tts, edge-tts, ssml, naturalidade, jarvis, pronuncia, clausula-petrea]
data: 2026-08-02
contexto: Cláusula pétrea exige comunicação contínua em áudio. O edge-tts já suporta SSML completo e o ecossistema precisa evoluir pronúncia e naturalidade sem trocar de TTS.
decisao: "Adicionei _ssml_enriquecer() em scripts/jarvis_bridge.py e mudei a ordem em gerar_audio(): phoneme primeiro sobre texto puro, depois SSML enriquece naturalidade."
impacto: "Números, percentuai

---
tipo: episodio
tags: [jarvis, bridge, celular, tailscale, websocket, voxumgrau, conectividade, validado]
data: 2026-08-04
fonte: tarefa
contexto: Usuario enfatizou que o importante e manter o Jarvis do celular conectado ao bridge. Verificacao de estado da ponte (PID 2676, porta 8765) e da conexao do celular.
decisao: Confirmado e documentado que o Jarvis do celular conecta ao bridge via rede Tailscale por WebSocket, de forma independente de ADB/USB. A conexao usa o IP fixo 100.64.71.9 e func

# ETAPA 26 — Jarvis v1 Release

## O que foi feito
- Auditoria completa de todos os componentes (18-25)
- Verificação de débito técnico (imports, duplicatas, dead code, secrets)
- Verificação de contratos entre componentes
- Auditoria de segurança (redaction, permissions, sandbox, circuit breaker)
- Auditoria de confiabilidade (circuit breaker, retry, recovery, degraded, watchdog, crash loop)
- Testes de sobrevivência (error → recovery → degraded → functional)
- Testes de segurança final (unauth

---
tipo: erro
tags: [widget, jarvis, unified-bridge, duplicacao, singleton]
data: 2026-08-18
contexto: Duas janelas "Jarvis Controle" visíveis na tela ao mesmo tempo
decisao: Encerrar o PID do widget_controle_jarvis.py (duplicado), manter o unified_bridge.py (canonico)
impacto: Uma unica janela Jarvis na tela; widget canonical respondendo HTTP 200
---

## Contexto

Usuário pediu para olhar a tela do PC e encontrar um erro. Havia duas janelas
"Jarvis Controle" abertas simultaneamente:

- PID 252
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]