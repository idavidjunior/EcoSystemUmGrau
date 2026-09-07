---
tipo: episodio
tags: [agenda, scheduler, spec, runtime-state]
data: 2026-09-07
contexto: pedido de spec para tarefas agendadas como extensão do runtime_state
decisao: spec proposta em specs/eco-tarefas-agendadas.spec.md com lista agendadas e tick idempotente
impacto: base pronta para implementar scripts/eco_agenda.py com migração do estado antigo
---

O runtime_state tem pendências simples sem horário nem recorrência.
O vigilante e o loop de desejos mostram o padrão de tick.
O schtasks já roda vigilante e guardiões neste host.
A spec nova estende o estado com lista agendada ativa.
Ela prevê ação permitida sem shell arbitrário por padrão.
