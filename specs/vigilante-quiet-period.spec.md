---
id: spec-vigilante-quiet-period
versao: 0.1.0
status: proposta
componente: scripts/vigilante.ps1
tags: [vigilante, git, commits, quiet-period, persistencia]
data: 2026-08-13
---

# Spec — Quiet Period do Vigilante

Spec de exemplo end-to-end da camada de specs. Documenta o comportamento do
quiet period do vigilante, implementado em `scripts/vigilante.ps1`.

## Objetivo

O vigilante agrupa commits em lotes após um período de silêncio no working tree
(15 min), com teto forçado de 1 hora para nunca ficar sem persistir.

## Requisitos

1. O vigilante só persiste o working tree do ecossistema quando ele está quieto
   há 15 minutos (`$quietPeriod = 900`), agrupando o trabalho em lotes.
2. Mesmo com atividade contínua, nunca passa mais de 1 hora sem persistir
   (`$maxInterval = 3600`, teto forçado).
3. O git sync do ecossistema roda a cada 5 minutos (`$gitInterval = 300`); o de
   projetos Android, a cada 1 minuto (`$projectGitInterval = 60`).
4. O PID e o log do vigilante ficam em `~/.vigilante.pid` e `~/.vigilante.log`.
5. A persistência delega ao gate de persistência (`scripts/persistencia.ps1`).

## Restrições

- Windows PowerShell 5.1 (script único, sem módulos externos).
- FileSystemWatcher via .NET para detecção de mudanças.
- Commit/push sempre executados pelo gate de persistência, nunca direto.
- UTF-8 nos logs.

## Dependências

- `scripts/persistencia.ps1` — gate de persistência (run-sync/commit).
- `scripts/ecosystem.ps1` — detecta o PID do vigilante via `~/.vigilante.pid`.
- `scripts/test-ecosystem.ps1` — valida o vigilante na suíte do ecossistema.

## Premissas

- Ambiente Windows com PowerShell 5.1 e git configurado.
- O repo do ecossistema tem remoto/upstream configurado para push.
- O usuário mantém o vigilante ativo (scheduled task EcoSystemVigilante).

## Entradas e Saídas

- Entrada: eventos do FileSystemWatcher no working tree; relógio do último
  sync por repositório.
- Saída: commits em lotes via gate; linhas de log em `~/.vigilante.log`.
- Efeito colateral: novas alterações no working tree após o commit do lote.

## Casos de Borda

- Working tree quieto: persiste no primeiro tick após o quiet period (15 min).
- Atividade contínua além de 1 h: commit forçado no teto (`maxInterval`).
- Sem pendências: nenhum commit é criado, sem erro.
- Repositório sem upstream: sync local funciona, push é ignorado.
- PID órfão (crash anterior): limpeza automática no start do vigilante.

## Critérios de Aceitação

- [arquivo:scripts/vigilante.ps1] Componente existe e é o alvo da spec.
- [arquivo:scripts/test-ecosystem.ps1] Teste do ecossistema existe (cobre o vigilante).
- [comando:python -c "import os,sys; sys.exit(0 if os.path.exists('scripts/vigilante.ps1') else 1)"] Componente existe e a verificação executável passa.
- Critério manual: com o working tree quieto, os commits agrupam o trabalho em lotes após ~15 min de silêncio.
- Critério manual: com atividade contínua, o intervalo entre commits nunca excede 1 h (teto forçado).

## Definition of Done

- [ ] Quiet period implementado em `scripts/vigilante.ps1` (`quietPeriod = 900`).
- [ ] Teto forçado implementado (`maxInterval = 3600`).
- [ ] `test-ecosystem.ps1` valida o vigilante (PID em `~/.vigilante.pid`).
- [ ] Evidências: log do vigilante mostra commits em lotes com quiet period.
- [ ] Código versionado via gate (`persistencia.ps1`).

## Riscos

- Atividade contínua gera commit forçado a cada 1 h — severidade baixa
  (mitigado pelo teto forçado; nunca perde persistência).
- Quiet period retém pendências por até 15 min — severidade baixa
  (intencional: agrupa trabalho em lotes).
- PID órfão de crash impede novo start — severidade média
  (mitigado por limpeza automática no start).

## Testes Relacionados

- scripts/test-ecosystem.ps1
