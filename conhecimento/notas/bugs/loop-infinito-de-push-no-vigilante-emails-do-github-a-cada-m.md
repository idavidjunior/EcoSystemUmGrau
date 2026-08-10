---
tags: [automacao, bug, constantemente, descoberta, opencode, projetos]
aliases: [Loop infinito de push no Vigilante (emails do GitHub a cada ]
date: 2026-08-10
---

# Loop infinito de push no Vigilante (emails do GitHub a cada minuto)

**Projeto:** opencode

## Causa Raiz
Usuário relatou receber emails do GitHub a cada minuto — algo estava subindo constantemente

## Correcao
---
tipo: bug
tags: [vigilante, github, git-sync, loop-infinito, memory-engine, push, automacao]
data: 2026-08-08
contexto: Usuário relatou receber emails do GitHub a cada minuto — algo estava subindo constantemente
decisao: Remover log de git-sync do loop do vigilante + excluir EcoSystemUmGrau da auto-descoberta de projetos
impacto: Sem pushes automáticos a cada 30-60s; vigilante volta a sincronizar só quando há mudança real (cooldown 5min)
---

# Loop infinito de push no Vigilante (emails do G
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[bug-hub-bugs]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[secrets-guard-no-preflightcheck]]