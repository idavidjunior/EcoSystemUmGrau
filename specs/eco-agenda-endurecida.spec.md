---
id: spec-eco-agenda-endurecida
versao: 0.1.0
status: ativa
componente: scripts/eco_agenda.py
tags: [agenda, seguranca, idempotencia, retry, scheduler, crash-recovery]
data: 2026-09-07
---

# Spec — Agenda Endurecida

## Objetivo

A agenda endurecida fecha o escape de caminho, garante execução única por vencimento e trata cada disparo como ciclo com estado e retry.

## Requisitos

1. O caminho de script passa por normalização com `realpath` e só executa dentro da raiz do repo.
2. Cada vencimento gera um disparo com id único e estados `pending`, `running`, `success` e `failed`.
3. A tarefa entra em `running` com escrita atômica antes de executar a ação.
4. O retry usa teto de tentativas com espera exponencial e só repete falha transitória.
5. A recuperação após crash marca `running` órfão como `failed` com motivo no próximo tick.
6. A idempotência usa chave por disparo e a ação repetida não duplica efeito observável.
7. O tick mantém a trava atual com detecção de dono morto e liberação segura.
8. Um processo confiável chama `executar_vencidas` periodicamente via schtasks com watchdog de inatividade.
9. O watchdog registra alerta quando nenhum tick conclui dentro da janela esperada.
10. A migração preserva tarefas antigas, marcando estado inicial `pending` sem perder histórico.

## Restrições

- Windows com PowerShell 5.1 e schtasks como motor de tick, com loop simples alternativo.
- Cliente em Python com apenas biblioteca padrão, sem dependência nova no runtime.
- Escrita atômica do estado com temporário mais `os.replace`, seguindo o runtime.
- Sem shell arbitrário em nenhuma hipótese, só ações permitidas e scripts do repo.
- Commit e push continuam exclusivos do gate de persistência, nunca na agenda.
- Respeito às cláusulas de ponto único de persistência, idioma pt-BR e deveres externos.

## Dependências

- `specs/eco-tarefas-agendadas.spec.md` — spec base que esta evolução estende sem duplicar.
- `scripts/eco_agenda.py` — cliente atual com escape e idempotência a corrigir.
- `scripts/security_engine.py` — validação de caminho e comando como segunda barreira.
- `scripts/tool_orchestrator.py` — padrão de retry com backoff e circuit breaker como referência.
- `scripts/mission_planner.py` — modelo `TaskStatus` como inspiração dos estados do disparo.
- schtasks do Windows como motor periódico com watchdog de inatividade.

## Premissas

- O escape foi confirmado com `../../` escapando da raiz no cálculo atual do caminho.
- A idempotência atual cobre ticks sobrepostos mas não crash no meio da ação.
- O retry distingue falha transitória de erro definitivo por prefixo do motivo.
- O watchdog usa o log de auditoria como prova de vida do tick.
- A tarefa antiga sem campo de estado migra para `pending` com próxima preservada.

## Entradas e Saídas

- Entrada: tarefa existente com vencimento, limites de retry e janela do watchdog.
- Saída: disparo com estado final, tentativas usadas, duração e motivo legível.
- Efeito colateral: estado com ciclo auditável, log de watchdog e próxima execução recalculada.

## Casos de Borda

- Caminho com `..` escapando da raiz: rejeita antes de qualquer execução.
- Link simbólico apontando para fora: o `realpath` revela e rejeita também.
- Crash com tarefa em `running`: próximo tick marca `failed` com motivo órfão.
- Falha transitória no limite: última tentativa vira `failed` sem nova agenda automática.
- Erro definitivo: não entra em retry e desativa a recorrência com motivo.
- Tick sem prova de vida na janela: watchdog emite alerta sem executar tarefa.
- Estado antigo sem disparos: migra para `pending` e segue o fluxo novo.

## Critérios de Aceitação

- [arquivo:specs/eco-agenda-endurecida.spec.md] Spec existe e é o documento desta entrega.
- [arquivo:scripts/eco_agenda.py] Cliente a endurecer existe.
- [comando:python -c "import ast; ast.parse(open('scripts/eco_agenda.py',encoding='utf-8').read())"] Cliente continua com sintaxe válida.
- Critério manual: script com `..` fora da raiz é rejeitado sem executar nada.
- Critério manual: crash simulado com `running` vira `failed` com motivo no tick seguinte.
- Critério manual: falha transitória repete com espera crescente até o teto configurado.

## Definition of Done

- [ ] Escape de caminho fechado com `realpath` e contenção na raiz.
- [ ] Ciclo de disparo com `pending`, `running`, `success` e `failed` implementado.
- [ ] Retry com teto e espera exponencial mais recuperação após crash.
- [ ] Processo periódico com watchdog de inatividade demonstrado em log.
- [ ] Código versionado no git via gate (`persistencia.ps1`).

## Riscos

- Ação não idempotente repetida no retry — severidade alta (mitigado por chave de disparo e ações com efeito único).
- Trava órfã bloqueando ticks — severidade média (mitigado por detecção de dono morto com teto de idade).
- Retry infinito mascarando erro real — severidade média (mitigado por teto de tentativas e erro definitivo sem retry).
- Watchdog cego sem prova de vida — severidade baixa (mitigado por auditoria com carimbo de tick concluído).
- Migração perdendo tarefa antiga — severidade média (mitigado por preservação com estado inicial `pending`).

## Testes Relacionados

- scripts/eco_agenda.py
- scripts/test_eco_agenda.py
- scripts/security_engine.py
