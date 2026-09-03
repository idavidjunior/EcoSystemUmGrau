---
tipo: decisao
tags: [auto-evolution, kernel, gate-veto, saude, evolucao]
data: 2026-09-03
contexto: Evoluir o auto_evolution.py (item 3) e o diagnóstico de saúde do ecossistema (item 4), sem duplicar estrutura existente (cláusula anti-Frankestein).
decisao:
  - Integrar o gate de veto do kernel (runtime_kernel.Kernel.gate_veto — Fase 2) ao ciclo fechado de evolução como novo estado STATE_BLOCKED_VETO / bloqueado_por_veto, consultado antes de delegar cada plano.
  - Adicionar o subcomando `health` ao auto_evolution.py que ORQUESTRA os checks existentes (preflight técnico, preflight ético, git status read-only, memória stats, checkpoint) em um relatório consolidado com veredito, sem duplicar a lógica dos checks.
  - Reutilizar a função _kernel_gate_veto fail-soft: se o kernel estiver indisponível, o plano segue aprovado (evolução não trava).
impacto:
  - A evolução autônoma agora respeita as regras de veto de governança (commit direto, destruição, segredos) de forma consistente com o roteamento de tarefas.
  - O ecossistema ganhou um diagnóstico único de saúde orquestrado sem criar versão paralela dos checks.
  - Comando `python scripts/auto_evolution.py health` validado: SAUDÁVEL. Preflight técnico: todos os testes passaram.
verificacao:
  - python scripts/auto_evolution.py health -> SAUDÁVEL
  - python scripts/preflight_check.py -> TODOS TESTES PASSARAM
  - _kernel_gate_veto('Evoluir capacidade de listar gaps') -> APROVADO
