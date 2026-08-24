---
tipo: padrao
tags: [widget, guardian, o-excl, psutil, corrida, ram-killer, fonte-unica]
data: 2026-08-21
contexto: Widget flutuante widget_edge.py (pywebview) morria silenciosamente em segundos ao rodar em background; loop eterno de reinicio do guardian a cada ~21s no guardian_log.txt.
decisao: |
  Diagnostico em cadeia (3 assassinos sobrepostos):
  1. Matador de RAM do guardian (get_kill_candidates) executava qualquer python/pythonw
     nao protegido com RAM livre < 500 MB (widget = 88 MB, alvo preferido).
  2. start_widget antigo fazia kill-first: cada reinicio MATAVA a instancia viva
     antes de gerar outra.
  3. Dois escritores no mesmo runtime/widget.pid com semanticas diferentes:
     widget usava como trava O_EXCL; guardian escrevia como registro e APAGAVA
     o arquivo julgado stale (update_protected_eco_pids unlink), mesmo com o
     dono vivo — permitindo que um desafiante roubasse a trava.

  Correcoes aplicadas:
  - system_guardian.py: fonte unica de verdade = tabela de processos via
    _pids_servicos_eco() com casamento por token terminando em "<script>.py"
    (imune a falsos positivos de wrappers powershell / python -c).
  - update_protected_eco_pids agora so varre processos; nunca le/apaga pid files.
  - kill_process bloqueia por cmdline (_pid_roda_script) + pid file: imune a
    corrida de gravacao.
  - start_widget sem kill-first e sem escrita na trava do widget.
  - is_narrador_up/is_tts_service_up/is_widget_up enxutos via token scan.
  - widget_edge.py instancia_unica: apos criar a trava com O_EXCL, confere se
    ja existe outro widget_edge vivo (defesa contra trava apagada externamente);
    perdedor sai sem tocar na trava do vencedor.
impacto: |
  Estado final verificado: 1 guardian (2864), 1 widget (7352, 89 MB, vivo),
  narrador/tts intactos, trava consistente com o dono, 65 s de observacao com
  zero reinicios/execucoes. Licoes gerais: (a) travas de instancia unica devem
  ter UM unico escritor; observadores usam a tabela de processos; (b) casamento
  de processo sempre por token sufixo .py, nunca substring solta; (c) protecao
  contra killer deve existir desde o instante zero do processo (cmdline), pois
  pid file tem janela de corrida entre spawn e gravacao; (d) pywebview importa
  como `import webview` e sob pythonw as streams sao None — redirecionar para
  log + faulthandler antes de qualquer print de biblioteca.

## Conexoes

- [[2026-08-04-tamanho-por-uso-real-iniciar-gui-com-pythonw-impl]]