---
titulo: Fix narrador triplicado e resiliência anti-órfão
tipo: decisao
tags: [narrador, thread-singleton, anti-orfao, watchdog, resiliencia]
data: 2026-08-31
status: RASCUNHO
resumo: |
  Narrador do widget_edge.py repetia cada evento 3x no log. Bug vinha do
  main() e poller() criarem 2 threads narradoras independentes. Fix:
  singleton thread-safe por PID + dedup em memória. Adicionado
  cleanup_duplicate_scripts() no system_guardian para detectar e matar
  PIDs duplicados do mesmo script.
contexto: |
  Narrador integrava log triplicado. Investigação: variável narrador_thread
  do poller era local e nunca recebia referência da thread do main, então
  poller sempre achava "narrador_thread is None" e criava outra.
decisao: |
  3 camadas: (1) singleton thread-safe _NARRADOR_LOCK + porta única
  iniciar_narrador_thread(); (2) dedup em memória no loop (set vistos);
  (3) cleanup_duplicate_scripts() no system_guardian detecta duplicatas.
testes_pendentes:
  - Reiniciar widget e verificar log do narrador sem triplicação
  - Confirmar que system_guardian.check_and_act mata duplicatas reais
  - Rodar preflight
arquivos_alterados:
  - scripts/widget_edge.py
  - scripts/system_guardian.py
