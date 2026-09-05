---
tags: [admin, cognitivo, env, general, hardcoded, restart]
aliases: [Adicionado passo 7/9 ao setup.bat que cria a task EcoSystemV]
date: 2026-09-05
---

# Adicionado passo 7/9 ao setup.bat que cria a task EcoSystemVigilante v

**Dominio:** general

Tipo: decisao

Tags: , setup, scheduled-task, portabilidade

Data: 2026-08-02

contexto: Vigilante estava inativo porque nenhum mecanismo criava a scheduled task. Corrigido manualmente; faltava fechar o ciclo no setup.bat para PCs novos.

decisao: Adicionado passo 7/9 ao setup.bat que cria a task EcoSystemVigilante via Register-ScheduledTask (AtLogOn, StartWhenAvailable, restart 3x, sem -Principal para nao exigir admin). Verificacao previa com schtasks /Query; se ja existir, pula.

Tipo: erro

Tags: , vigilante, scheduled-task, bootstrap, windows

Data: 2026-08-02

contexto: Status do ecossistema reportava "Vigilante: INATIVO" sem PID e sem log.

decisao: Diagnosticado que nenhum mecanismo criava a scheduled task. Criada task via Register-ScheduledTask (AtLogOn, sem -Principal para nao exigir admin), profile.ps1 recriado com as funcoes (start/stop/status-vigilante + ecosystem), path hardcoded corrigido para $env:USERPROFILE.

impacto: Vigilante agora inicia no l
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]