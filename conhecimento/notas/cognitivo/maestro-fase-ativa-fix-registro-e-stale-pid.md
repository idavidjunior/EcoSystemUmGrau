---
tags: [bloqueia, cognitivo, duplicatas, general, libera, registra]
aliases: [Maestro Fase Ativa - Fix Registro e Stale PID]
date: 2026-08-31
---

# Maestro Fase Ativa - Fix Registro e Stale PID

**Dominio:** general

## Problema
- Maestro nao verificava se PID registrado ainda estava vivo
- Guardian nao registrava PID no Maestro apos iniciar servico
- Guardians simultaneos nao eram bloqueados

## Solucao
1. 
untime_maestro.py:pode_iniciar(): adicionar psutil.pid_exists() antes de bloquear
2. system_guardian.py: trocar decisao_local="nasceu" por "registrar_nascimento"
3. system_guardian.py:_observar_no_maestro(): aceitar "registrar_nascimento" no registro

## Teste
- End-to-end: TTS morre -> guardian consulta Maestro -> Maestro libera -> guardian registra -> bloqueia duplicatas
- Funciona com 4 guardians simultaneos
- Stale PID (99999) e limpo automaticamente
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]