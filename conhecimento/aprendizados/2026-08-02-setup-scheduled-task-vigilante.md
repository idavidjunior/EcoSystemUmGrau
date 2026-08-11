---
tipo: decisao
tags:
  - setup
  - scheduled-task
  - portabilidade
data: 2026-08-02
contexto: Vigilante estava inativo porque nenhum mecanismo criava a scheduled task. Corrigido manualmente; faltava fechar o ciclo no setup.bat para PCs novos.
decisao: Adicionado passo 7/9 ao setup.bat que cria a task EcoSystemVigilante via Register-ScheduledTask (AtLogOn, StartWhenAvailable, restart 3x, sem -Principal para nao exigir admin). Verificacao previa com schtasks /Query; se ja existir, pula.
impacto: Nova maquina + setup.bat agora tem o guardiao automatico desde o boot. Setup completo 9 passos (6 profile, 7 task, 8 keys, 9 validacao).
detalhe: schtasks /Create com escape \" no caminho com espacos falhou com "Acesso negado" â€” usar Register-ScheduledTask via powershell -Command, que registra no contexto do usuario atual sem elevacao.

## Conexoes

- [[cluster-hub-programacao]]