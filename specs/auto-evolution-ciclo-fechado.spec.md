---
id: spec-auto-evolution-ciclo-fechado
versao: 0.1.0
status: proposta
componente: scripts/auto_evolution.py
tags: [auto-evolution, autonomia, subagente, ler, quality-gates, evolucao]
data: 2026-08-28
---

# Spec — Ciclo Fechado de Auto-Evolução

## Objetivo

Fechar o ciclo de auto-evolução do EcoSystemUmGrau: transformar o
`auto_evolution.py` de um gerador de relatórios e dry-runs em um executor real
de evoluções. O motor deve, ao detectar um gap de alta prioridade, delegar a
execução do plano a um subagente (opencode run ou LER), validar o resultado
com os gates obrigatórios (preflight_check + preflight_etica), rodar testes,
fazer rollback em caso de falha e persistir o aprendizado.

## Requisitos

1. O `auto_evolution.py evolve --apply` deve executar planos de alta prioridade
   de verdade (não apenas documentar/dry-run como hoje).
2. A execução de um plano deve ser delegada a um subagente externo
   (opencode run --agent ou LER), nunca feita inline pelo motor.
3. Após a execução, o motor deve validar as mudanças com
   `python scripts/preflight_check.py` e `python scripts/preflight_etica.py`.
4. Se o preflight falhar, o motor deve reverter as mudanças (rollback) e
   registrar a falha como memória de tipo `erro`.
5. Cada evolução executada deve ser persistida como memória (kind `decisao`)
   e registrada no estado de evolução (`runtime/learning/evolution/`).
6. O motor deve suportar execução segura por padrão: `--dry-run` (atual),
   `--apply`, `--apply --no-preflight` (para auditoria manual) e
   `--max-plans N` (limite de planos por ciclo).
7. O ciclo deve registrar qual subagente executou cada plano, com o comando
   usado e o status (sucesso/rollback).

## Restrições

- Script 100% stdlib Python (sem dependências novas).
- Respeitar a cláusula do ponto único de persistência: todo git commit/push
  passa por `scripts/persistencia.ps1`, nunca git direto.
- Respeitar a cláusula de autonomia informada: o motor nunca evolui em
  silêncio — comunica antes, durante e depois.
- Execução de subagente com timeout (nunca travar o motor).
- Não quebrar a compatibilidade dos comandos existentes (`scan`, `gaps`,
  `plan`, `assess`, `status`).
- Windows PowerShell 5.1 como shell de execução.
- Não executar planos de risco alto sem confirmação explícita (flag `--force`).

## Dependências

- `scripts/auto_evolution.py` — motor a ser aprimorado.
- `scripts/preflight_check.py` — gate técnico obrigatório.
- `scripts/preflight_etica.py` — gate ético obrigatório.
- `scripts/persistencia.ps1` — gate de persistência (git).
- `scripts/runtime_state.py` — checkpoint/restore para rollback.
- `scripts/memory_engine.py` — persistência de aprendizados.
- `scripts/behavior_slices.py` — rastreio dos fluxos executados.
- `opencode` CLI — subagente de execução (`opencode run --agent`).
- LER (`ler`) — alternativa de execução para tarefas complexas (Rota B).

## Premissas

- Python 3 disponível no PATH.
- `opencode` CLI disponível no PATH (usado para o subagente de execução).
- NVIDIA_API_KEY disponível (já configurada no ecossistema).
- O working directory de execução é a raiz do EcoSystemUmGrau.

## Entradas e Saídas

- **Entrada**: comando CLI `auto_evolution.py evolve` com flags
  (`--apply`, `--dry-run`, `--max-plans N`, `--force`, `--no-preflight`).
- **Saída**: relatório da execução com status por plano
  (executado_sucesso / rollback / pulado / bloqueado_por_risco).
- **Efeito colateral**: mudanças reais no codebase, memórias persistidas,
  state de evolução atualizado, possíveis commits via gate.

## Casos de Borda

- Nenhum plano de alta prioridade disponível → relatório vazio, sem ação.
- Subagente de execução indisponível (opencode/LER não instalado) → bloqueia
  a execução e reporta como `bloqueado_externo`.
- Preflight falha após execução → rollback automático + memória de erro.
- Rollback falha (estado corrompido) → preserva estado seguro, reporta bloqueio.
- Plano de risco alto sem `--force` → pulado com justificativa.
- Timeout do subagente → marca como `timeout`, não trava o ciclo.
- Plano que não altera arquivos (documentado) → reportado como `sem_mudanca`.
- Concorrência: dois `evolve --apply` ao mesmo tempo → lock por repositório
  via gate de persistência.

## Critérios de Aceitação

- [arquivo:scripts/auto_evolution.py] Motor suporta `--apply` executando subagente.
- [arquivo:scripts/auto_evolution.py] Motor valida com preflight_check + preflight_etica.
- [arquivo:scripts/auto_evolution.py] Motor faz rollback se preflight falhar.
- [comando:python scripts/auto_evolution.py evolve --dry-run] Dry-run retorna exit 0 sem mudanças.
- [comando:python scripts/auto_evolution.py evolve --apply --max-plans 0] Sem planos não executa nada.
- [comando:python scripts/auto_evolution.py scan] Scan existente continua funcionando.
- [comando:python scripts/auto_evolution.py gaps] Gaps continua funcionando.
- Critério manual 1 — relatório lista status por plano (executado/rollback/pulado).
- Critério manual 2 — memória de tipo `decisao` é criada para cada evolução aplicada.
- Critério manual 3 — memória de tipo `erro` é criada em caso de rollback.
- Critério manual 4 — execução de subagente registra o comando e o status.

## Definition of Done

- [ ] Motor executa planos via subagente com validação e rollback.
- [ ] Comandos existentes (scan/gaps/plan/assess/status) mantêm compatibilidade.
- [ ] Testes dos novos comandos executados e aprovados.
- [ ] Evidências de funcionamento coletadas (dry-run e apply controlado).
- [ ] Código versionado no git via gate (`persistencia.ps1`).

## Riscos

- Subagente executa mudança não desejada — severidade média, mitigado por
  `--dry-run` padrão, preflight obrigatório e rollback.
- Rollback incompleto deixa estado inconsistente — severidade alta, mitigado
  por checkpoint pré-execução (runtime_state) e preservação de estado seguro.
- Loop infinito de evolução — severidade média, mitigado por `--max-plans`.
- Execução destrutiva sem supervisão — severidade alta, mitigado por bloqueio
  de planos de risco alto sem `--force` e comunicação obrigatória.

## Testes Relacionados

- `scripts/auto_evolution.py evolve --dry-run` (teste manual de segurança)
- `scripts/auto_evolution.py evolve --apply --max-plans 1` (teste controlado)
- `scripts/preflight_check.py` (validação dos gates)
- `scripts/preflight_etica.py` (validação ética)