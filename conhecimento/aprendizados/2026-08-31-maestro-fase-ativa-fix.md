---
tipo: decisao
tags: [maestro, runtime, guardian, fase-ativa, stale-pid]
data: 2026-08-31
contexto: |
  Maestro de Runtime em fase ativa. Guardians consultam antes de iniciar servicos.
  Bug: Maestro nao verificava se PID registrado ainda estava vivo (confiava cego no campo vivo).
  Bug: Guardian nao registrava PID no Maestro apos iniciar servico.
decisao: |
  1. Adicionar verificacao de vida (psutil.pid_exists) no pode_iniciar() do Maestro.
     Se PID registrado morto, limpar registro stale e liberar restart.
  2. Trocar decisao_local de "nasceu" para "registrar_nascimento" no guardian.
     Isso faz o Maestro registrar o PID apos o servico nascer.
  3. A aceitar "registrar_nascimento" na condicao de registro do _observar_no_maestro.
impacto: |
  Guardian agora obedece Maestro em fase ativa. TTS nao e duplicado.
  Stale PIDs sao limpos automaticamente. Cooldown previne restart imediato.
---
# Maestro Fase Ativa - Fix Registro e Stale PID

## Problema
- Maestro nao verificava se PID registrado ainda estava vivo
- Guardian nao registrava PID no Maestro apos iniciar servico
- Guardians simultaneos nao eram bloqueados

## Solucao
1. untime_maestro.py:pode_iniciar(): adicionar psutil.pid_exists() antes de bloquear
2. system_guardian.py: trocar decisao_local="nasceu" por "registrar_nascimento"
3. system_guardian.py:_observar_no_maestro(): aceitar "registrar_nascimento" no registro

## Teste
- End-to-end: TTS morre -> guardian consulta Maestro -> Maestro libera -> guardian registra -> bloqueia duplicatas
- Funciona com 4 guardians simultaneos
- Stale PID (99999) e limpo automaticamente
