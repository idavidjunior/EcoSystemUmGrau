---
id: spec-eco-tarefas-agendadas
versao: 0.1.0
status: ativa
componente: scripts/eco_agenda.py
tags: [agenda, scheduler, runtime-state, care, automacao]
data: 2026-09-07
---

# Spec — Tarefas Agendadas

## Objetivo

O agendador estende o runtime_state com tarefas agendadas, executando ações na hora certa com auditoria e sem travar o ecossistema.

## Requisitos

1. O estado ganha a lista `agendadas` com id, nome, ação, recorrência, próxima execução, última execução e flag ativa.
2. O cliente vive em `scripts/eco_agenda.py` e expõe `agendar`, `listar`, `cancelar` e `executar_vencidas`.
3. As recorrências suportadas são execução única, intervalo em segundos e janela diária com hora de início e fim.
4. As ações nascem de lista permitida com nota, checkpoint e comando de script do repo como padrão.
5. Cada tick executa só o que venceu, com trava contra dupla execução concorrente.
6. Cada execução respeita timeout próprio e registra auditoria em `runtime/agenda.log`.
7. Tarefa sem próxima execução válida é desativada com motivo em vez de falhar em silêncio.
8. O EcoClient ganha métodos opcionais que delegam à agenda sem mudar a interface existente.
9. O tick roda via schtasks ou loop simples, reaproveitando o padrão do vigilante e do loop de desejos.
10. A migração preserva o estado antigo, adicionando a lista vazia quando ela não existe.

## Restrições

- Windows com PowerShell 5.1 e schtasks opcional, com loop simples como alternativa.
- Cliente em Python com apenas biblioteca padrão, sem dependência nova no runtime.
- Escrita atômica do estado com temporário mais `os.replace`, seguindo o runtime.
- Sem shell arbitrário por padrão, só ações permitidas e scripts do repo.
- Commit e push continuam exclusivos do gate de persistência, nunca na agenda.
- Respeito às cláusulas de ponto único de persistência, idioma pt-BR e deveres externos.

## Dependências

- `scripts/runtime_state.py` — funções `load_state` e `save_state` mais lista `pending` como modelo.
- `scripts/eco_client.py` — ponto de integração programática que delega à agenda.
- `scripts/vigilante.ps1` — padrão de tick periódico e tarefa schtasks como referência.
- `scripts/desejos_loop.py` — padrão de intervalo com janela de horário como referência.
- `scripts/mission_planner.py` — modelo de missão e prioridade como inspiração de ação.
- schtasks do Windows como motor de tick quando disponível no host.

## Premissas

- O host é Windows com Python 3 e fuso local como referência de horário.
- O estado antigo sem a lista `agendadas` continua válido e migra sozinho.
- A agenda trata ação desconhecida como erro de validação antes de agendar.
- O tick é idempotente e pode rodar a cada minuto sem duplicar execução.
- A janela diária usa hora local com início inclusivo e fim exclusivo.

## Entradas e Saídas

- Entrada: nome, ação permitida, parâmetros, recorrência, horário e flag ativa.
- Saída: dicionários com `ok`, tarefa criada, lista filtrada e resultado por execução.
- Efeito colateral: estado atualizado, auditoria em log e checkpoint quando a ação pede.

## Casos de Borda

- Estado antigo sem lista: cria a lista vazia e segue sem erro.
- Ação desconhecida: rejeita no agendamento com motivo explícito.
- Horário inválido: rejeita com motivo em vez de agendar torto.
- Tick sem vencidas: retorna vazio sem tocar no estado.
- Execução que estoura o tempo: marca timeout e agenda a próxima sem travar.
- Dois ticks concorrentes: a trava serializa e só um executa cada tarefa.
- Relógio com horário passado: executa uma vez e recalcula a próxima.

## Critérios de Aceitação

- [arquivo:specs/eco-tarefas-agendadas.spec.md] Spec existe e é o documento desta entrega.
- [arquivo:scripts/runtime_state.py] Estado base referenciado existe.
- [comando:python -c "import ast; ast.parse(open('scripts/runtime_state.py',encoding='utf-8').read())"] Estado base continua com sintaxe válida.
- Critério manual: agendar nota recorrente cria tarefa ativa com próxima execução válida.
- Critério manual: tick com tarefa vencida executa uma vez e recalcula a próxima.
- Critério manual: nenhuma mudança visual ou de interface acompanha a entrega da agenda.

## Definition of Done

- [ ] Cliente implementado em `scripts/eco_agenda.py` conforme os requisitos.
- [ ] Estado estendido com lista `agendadas` e migração do estado antigo.
- [ ] Integração opcional via EcoClient sem quebrar a API existente.
- [ ] Evidências: agendamento e tick com execução vencida demonstrados em log.
- [ ] Código versionado no git via gate (`persistencia.ps1`).

## Riscos

- Dupla execução por ticks sobrepostos — severidade média (mitigado por trava e marcação de última execução).
- Ação perigosa via agenda — severidade alta (mitigado por lista permitida sem shell arbitrário).
- Estado corrompido por escrita concorrente — severidade média (mitigado por escrita atômica existente).
- Tick silencioso que nunca executa — severidade baixa (mitigado por auditoria e próxima execução visível).
- Complexidade excessiva antes da necessidade — severidade média (mitigado por três recorrências mínimas).

## Testes Relacionados

- scripts/runtime_state.py
- scripts/eco_client.py
- scripts/test_eco_client.py
