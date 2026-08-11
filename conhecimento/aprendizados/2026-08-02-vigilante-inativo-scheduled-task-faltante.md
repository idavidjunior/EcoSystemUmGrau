---
tipo: erro
tags:
  - vigilante
  - scheduled-task
  - bootstrap
  - windows
data: 2026-08-02
contexto: Status do ecossistema reportava "Vigilante: INATIVO" sem PID e sem log.
decisao: Diagnosticado que nenhum mecanismo criava a scheduled task. Criada task via Register-ScheduledTask (AtLogOn, sem -Principal para nao exigir admin), profile.ps1 recriado com as funcoes (start/stop/status-vigilante + ecosystem), path hardcoded corrigido para $env:USERPROFILE.
impacto: Vigilante agora inicia no logon e em nova sessao; correcao portavel e consistente com o setup.bat.
detalhe: schtasks /Create falhou com "argumento invalido" por causa de aspas no caminho com espaco - Register-ScheduledTask evitou o problema. Register-ScheduledTask com -Principal exigia admin (Acesso negado); sem -Principal registra no contexto do usuario atual.
