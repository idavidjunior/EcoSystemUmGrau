---
tipo: padrao
tags: [resiliencia, widget, jarvis, unified-bridge, singleton, watchdog, autocurativo]
data: 2026-08-18
contexto: Usuário pediu para o ecossistema se tornar resiliente contra erros como o de dois widgets Jarvis abertos simultaneamente, corrigindo automaticamente sem pedido
decisao: Adicionar travas de instância única em 3 camadas: guarda no widget antigo, limpeza cruzada no canonical, e verificação contínua no watchdog
impacto: Duplicação de widget/processos Jarvis é detectada e corrigida sozinha; nenhum processo canônico é afetado
---

## Contexto

Ocorreu duplicação: dois widgets "Jarvis Controle" na tela (PID 2528 unified_bridge.py + PID 5408 widget_controle_jarvis.py). O unified_bridge.py já tinha lock de instância única, mas o widget antigo não tinha proteção nenhuma e podia abrir por cima.

## Correção aplicada (3 camadas)

1. `scripts/widget_controle_jarvis.py` — nova função `_garantir_instancia_unica()` chamada no início do `main()`:
   - Se `unified_bridge.py` (canônico) já roda, o widget antigo sai (exit 0).
   - Se já existe outra cópia do próprio widget, a mais nova sai.

2. `scripts/unified_bridge.py` — `_cleanup_duplicate_processes()` estendida:
   - Passou a varrer `python.exe` E `pythonw.exe` (antes só python.exe).
   - Além de limpar duplicatas do próprio unified_bridge, também mata o widget antigo (`widget_controle_jarvis.py`) na inicialização — pois é o canônico e o antigo não deve rodar separado.

3. `scripts/watchdog.ps1` — nova seção "WIDGET JARVIS UNICO" no loop:
   - Caso A: unified_bridge ativo + widget antigo ativo → mata o widget antigo.
   - Caso B: unified_bridge inativo + 2+ widgets antigos → mantém o mais antigo, mata as demais cópias.
   - Registra cada correção no log.

## Validação

- `python -m py_compile` nos dois scripts: OK.
- Parser PowerShell no watchdog.ps1: OK.
- Teste real: com unified_bridge ativo, `python widget_controle_jarvis.py` recusou abrir com "unified_bridge.py já ativo...".
- `preflight_check.py`: TODOS TESTES PASSARAM.
- Watchdog reiniciado (PID 11212) e unified_bridge reiniciado com código novo (PID 12268), janela única "Jarvis Controle", HTTP 200.

## Lição

Processos com versão canônica consolidada devem ter proteção de instância única em TODAS as camadas: no próprio script (guarda), no canônico (limpeza cruzada) e no supervisor (watchdog). Nenhuma camada sozinha é suficiente se outra via de inicialização existir (boot, atalho, watchdog).
