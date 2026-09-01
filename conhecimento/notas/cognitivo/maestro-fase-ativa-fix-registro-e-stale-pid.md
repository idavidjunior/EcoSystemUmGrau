---
tags: [campo, cego, cognitivo, confiava, general, vivo]
aliases: [Maestro Fase Ativa - Fix Registro e Stale PID]
date: 2026-08-31
---

# Maestro Fase Ativa - Fix Registro e Stale PID

**Dominio:** general

﻿---
tipo: decisao
tags: [maestro, runtime, guardian, fase-ativa, stale-pid]
data: 2026-08-31
contexto: |
  Maestro de Runtime em fase ativa. Guardians consultam antes de iniciar servicos.
  Bug: Maestro nao verificava se PID registrado ainda estava vivo (confiava cego no campo vivo).
  Bug: Guardian nao registrava PID no Maestro apos iniciar servico.
decisao: |
  1. Adicionar verificacao de vida (psutil.pid_exists) no pode_iniciar() do Maestro.
     Se PID registrado morto, limpar registro stal
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]