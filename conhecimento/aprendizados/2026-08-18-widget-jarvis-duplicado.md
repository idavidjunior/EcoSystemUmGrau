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

- PID 2528 — `python.exe scripts/unified_bridge.py` (iniciado 20:14, janela à direita)
- PID 5408 — `pythonw.exe scripts/widget_controle_jarvis.py` (iniciado 20:43 pelo boot do Eco, janela à esquerda)

## Causa

A memória já registrava a arquitetura canônica:
- `scripts/unified_bridge.py` é a ponte única (narrador + TTS service + widget, com singleton lock).
- `scripts/widget_controle_jarvis.py` é o widget antigo que NÃO deve rodar separado.

O boot do Eco abriu o widget antigo por cima do unified_bridge já em execução.
Cada script só limpa duplicatas da própria classe, então não se cancelaram.

## Correção

- `taskkill /PID 5408 /F` encerrou o duplicado.
- Mantido PID 2528 (unified_bridge), que responde `http://127.0.0.1:16232/widget_unified.html` com HTTP 200.

## Lição

Antes de abrir qualquer widget/ponte, verificar se já existe o processo canônico
rodando (unified_bridge.py) e não abrir o widget antigo separado. Consultar a
memória antes de iniciar processos que possuem versão canônica consolidada.

## Conexoes

- [[2026-08-04-tamanho-por-uso-real-iniciar-gui-com-pythonw-impl]]
- [[aprendizado-2026-07-31-horas-faladas-corretamente-no-tts-do-]]