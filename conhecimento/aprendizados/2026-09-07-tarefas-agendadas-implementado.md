---
tipo: episodio
tags: [agenda, scheduler, implementacao, runtime-state]
data: 2026-09-07
contexto: implementação das tarefas agendadas como extensão do runtime_state
decisao: eco_agenda com agendar e tick idempotente mais migração sem tocar o núcleo
impacto: runtime ganha ações na hora certa com auditoria e trava concorrente
---

O cliente vive em scripts e eco agenda. Ele migra o estado sozinho.
Ele aceita execução única e intervalo e janela diária simples.
Ele só roda ação permitida sem shell arbitrário por padrão.
O teste isolado passou com estado temporário sem poluir o real.
O EcoClient ganhou agenda sem quebrar a API antiga.
